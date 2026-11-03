from decimal import Decimal as D
from pathlib import Path

from conftest import make_invoice

from freight_audit.audit import (
    Summary,
    audit_all,
    audit_invoice,
    expected_charge,
    load_invoices,
    summarize,
    write_invoices,
    write_report,
)
from freight_audit.tariff import TariffTable


def test_hand_computed_case(table: TariffTable) -> None:
    # See docs/derivation.md section 5: 20 kg * 4.80 = 96.00; fuel 18.5% = 17.76
    exp = expected_charge(make_invoice("0", "0"), table)
    assert exp.chargeable_kg == D("20.0")
    assert exp.freight == D("96.00")
    assert exp.fuel == D("17.76")
    assert exp.total == D("113.76")
    assert not exp.minimum_applied


def test_minimum_charge_applies(table: TariffTable) -> None:
    inv = make_invoice("0", "0", actual="1")
    inv = inv.__class__(
        **{**inv.__dict__, "length_cm": D(10), "width_cm": D(10), "height_cm": D(10)}
    )
    exp = expected_charge(inv, table)
    assert exp.minimum_applied
    assert exp.freight == D("75.00")
    assert exp.fuel == D("13.88")


def test_ok_invoice(table: TariffTable) -> None:
    f = audit_invoice(make_invoice("96.00", "17.76"), table)
    assert f.status == "ok"
    assert f.reasons == ()


def test_overcharge_on_actual_weight_divisor_error(table: TariffTable) -> None:
    # billed using divisor 5000 -> 24 kg * 4.80 = 115.20, fuel 21.31
    f = audit_invoice(make_invoice("115.20", "21.31"), table)
    assert f.status == "overcharge"
    assert f.difference == D("22.75")
    assert f.reasons == ("freight", "fuel")


def test_undercharge(table: TariffTable) -> None:
    f = audit_invoice(make_invoice("90.00", "17.76"), table)
    assert f.status == "undercharge"
    assert f.reasons == ("freight",)


def test_summary_and_io(table: TariffTable, tmp_path: Path) -> None:
    invs = [
        make_invoice("96.00", "17.76"),
        make_invoice("115.20", "21.31"),
        make_invoice("90.00", "17.76"),
    ]
    findings = audit_all(invs, table)
    s = summarize(findings)
    assert (s.invoices, s.flagged_overcharges, s.flagged_undercharges) == (3, 1, 1)
    assert s.recoverable == D("22.75")
    assert any("Recoverable overcharge:  22.75" in line for line in s.lines())
    p = tmp_path / "i.csv"
    write_invoices(invs, p)
    assert load_invoices(p) == invs
    r = tmp_path / "r.csv"
    write_report(findings, r)
    assert r.read_text().count("\n") == 4


def test_empty_summary_lines() -> None:
    s = Summary(0, 0, 0, D(0), D(0), D(0))
    assert "0.00%" in s.lines()[1]
