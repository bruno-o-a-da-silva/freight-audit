"""Recompute expected charges and compare them with billed invoices."""

import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from freight_audit.tariff import TariffTable
from freight_audit.weight import chargeable_weight_kg

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Invoice:
    # cm, kg, and invoice currency

    invoice_id: str
    lane: str
    mode: str
    actual_kg: Decimal
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    billed_freight: Decimal
    billed_fuel: Decimal

    @property
    def billed_total(self) -> Decimal:
        return self.billed_freight + self.billed_fuel


@dataclass(frozen=True)
class Expected:
    chargeable_kg: Decimal
    rate_per_kg: Decimal
    freight: Decimal
    fuel: Decimal
    minimum_applied: bool

    @property
    def total(self) -> Decimal:
        return self.freight + self.fuel


@dataclass(frozen=True)
class Finding:
    invoice: Invoice
    expected: Expected
    difference: Decimal  # billed - expected; positive means overcharge
    status: str  # "ok", "overcharge" or "undercharge"
    reasons: tuple[str, ...]


def expected_charge(
    inv: Invoice, table: TariffTable, increment_kg: Decimal = Decimal("0.5")
) -> Expected:
    # Fuel is a percentage of freight after the minimum, not of the linehaul.
    t = table.lookup(inv.lane, inv.mode)
    ckg = chargeable_weight_kg(
        inv.actual_kg,
        inv.length_cm,
        inv.width_cm,
        inv.height_cm,
        t.divisor_cm3_per_kg,
        increment_kg,
    )
    rate = t.rate_for(ckg)
    linehaul = ckg * rate
    minimum_applied = linehaul < t.minimum_charge
    freight = money(t.minimum_charge if minimum_applied else linehaul)
    fuel = money(freight * t.fuel_surcharge_pct / Decimal(100))
    return Expected(ckg, rate, freight, fuel, minimum_applied)


def audit_invoice(inv: Invoice, table: TariffTable, tolerance: Decimal = CENT) -> Finding:
    exp = expected_charge(inv, table)
    diff = money(inv.billed_total - exp.total)
    reasons: list[str] = []
    if abs(inv.billed_freight - exp.freight) > tolerance:
        reasons.append("freight")
    if abs(inv.billed_fuel - exp.fuel) > tolerance:
        reasons.append("fuel")
    status = "ok" if abs(diff) <= tolerance else "overcharge" if diff > 0 else "undercharge"
    return Finding(inv, exp, diff, status, tuple(reasons))


def audit_all(invoices: list[Invoice], table: TariffTable) -> list[Finding]:
    return [audit_invoice(i, table) for i in invoices]


@dataclass(frozen=True)
class Summary:
    invoices: int
    flagged_overcharges: int
    flagged_undercharges: int
    billed_total: Decimal
    expected_total: Decimal
    recoverable: Decimal  # sum of overcharges only

    def lines(self) -> list[str]:
        rate = (
            Decimal(self.flagged_overcharges) / Decimal(self.invoices) * 100
            if self.invoices
            else Decimal(0)
        )
        return [
            f"Invoices audited:        {self.invoices}",
            f"Overcharges flagged:     {self.flagged_overcharges} ({money(rate)}%)",
            f"Undercharges flagged:    {self.flagged_undercharges}",
            f"Billed total:            {money(self.billed_total)}",
            f"Expected total:          {money(self.expected_total)}",
            f"Recoverable overcharge:  {money(self.recoverable)}",
        ]


def summarize(findings: list[Finding]) -> Summary:
    return Summary(
        invoices=len(findings),
        flagged_overcharges=sum(1 for f in findings if f.status == "overcharge"),
        flagged_undercharges=sum(1 for f in findings if f.status == "undercharge"),
        billed_total=sum((f.invoice.billed_total for f in findings), Decimal(0)),
        expected_total=sum((f.expected.total for f in findings), Decimal(0)),
        recoverable=sum((f.difference for f in findings if f.status == "overcharge"), Decimal(0)),
    )


INVOICE_FIELDS = [
    "invoice_id",
    "lane",
    "mode",
    "actual_kg",
    "length_cm",
    "width_cm",
    "height_cm",
    "billed_freight",
    "billed_fuel",
]

REPORT_FIELDS = [
    "invoice_id",
    "lane",
    "mode",
    "chargeable_kg",
    "rate_per_kg",
    "minimum_applied",
    "expected_freight",
    "expected_fuel",
    "expected_total",
    "billed_total",
    "difference",
    "status",
    "reasons",
]


def load_invoices(path: Path) -> list[Invoice]:
    with path.open(newline="") as fh:
        return [
            Invoice(
                invoice_id=r["invoice_id"],
                lane=r["lane"],
                mode=r["mode"],
                actual_kg=Decimal(r["actual_kg"]),
                length_cm=Decimal(r["length_cm"]),
                width_cm=Decimal(r["width_cm"]),
                height_cm=Decimal(r["height_cm"]),
                billed_freight=Decimal(r["billed_freight"]),
                billed_fuel=Decimal(r["billed_fuel"]),
            )
            for r in csv.DictReader(fh)
        ]


def write_invoices(invoices: list[Invoice], path: Path) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(INVOICE_FIELDS)
        for i in invoices:
            w.writerow([getattr(i, f) for f in INVOICE_FIELDS])


def write_report(findings: list[Finding], path: Path) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(REPORT_FIELDS)
        for f in findings:
            e = f.expected
            w.writerow(
                [
                    f.invoice.invoice_id,
                    f.invoice.lane,
                    f.invoice.mode,
                    e.chargeable_kg,
                    e.rate_per_kg,
                    e.minimum_applied,
                    e.freight,
                    e.fuel,
                    e.total,
                    f.invoice.billed_total,
                    f.difference,
                    f.status,
                    ";".join(f.reasons),
                ]
            )
