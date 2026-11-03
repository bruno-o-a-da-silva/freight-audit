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


def test_document_envelope_pays_the_minimum(table: TariffTable) -> None:
    # 30 x 20 x 5 cm, 0.8 kg: billed weight 1.0 kg, 4.80 is far below the 75.00 minimum.
    # Fuel 75.00 * 0.185 = 13.875, rounds half-up to 13.88.
    exp = expected_charge(make_invoice("0", "0", actual="0.8", dims=("30", "20", "5")), table)
    assert exp.chargeable_kg == D("1.0")
    assert exp.minimum_applied
    assert exp.freight == D("75.00")
    assert exp.fuel == D("13.88")


def test_rounding_up_pushes_44_8_kg_into_the_45_kg_break(table: TariffTable) -> None:
    # Found while checking by hand: 44.8 kg rounds to 45.0 and gets the cheaper rate,
    # so the invoice total is lower than 44.8 * 4.80 = 215.04.
    exp = expected_charge(make_invoice("0", "0", actual="44.8", dims=("40", "30", "30")), table)
    assert exp.chargeable_kg == D("45.0")
    assert exp.rate_per_kg == D("4.08")
    assert exp.freight == D("183.60")
    assert exp.fuel == D("33.97")


def test_fractional_dimensions_from_the_warehouse_scale(table: TariffTable) -> None:
    # 60.5 x 50.2 x 40.1 cm = 121,786.21 cm3 / 6000 = 20.297... kg -> 20.5 kg
    exp = expected_charge(
        make_invoice("0", "0", actual="12.3", dims=("60.5", "50.2", "40.1")), table
    )
    assert exp.chargeable_kg == D("20.5")
    assert exp.freight == D("98.40")


def test_invoice_billed_correctly_is_ok(table: TariffTable) -> None:
    f = audit_invoice(make_invoice("96.00", "17.76"), table)
    assert f.status == "ok"
    assert f.reasons == ()


def test_carrier_used_divisor_5000_instead_of_6000(table: TariffTable) -> None:
    # billed using divisor 5000 -> 24 kg * 4.80 = 115.20, fuel 21.31
    f = audit_invoice(make_invoice("115.20", "21.31"), table)
    assert f.status == "overcharge"
    assert f.difference == D("22.75")
    assert f.reasons == ("freight", "fuel")


def test_freight_short_billed_by_six(table: TariffTable) -> None:
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


def test_summary_of_empty_file_does_not_divide_by_zero() -> None:
    s = Summary(0, 0, 0, D(0), D(0), D(0))
    assert "0.00%" in s.lines()[1]
