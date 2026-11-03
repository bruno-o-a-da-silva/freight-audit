"""Made-up tariffs and invoices for testing. Rates are invented, not from any carrier."""

import random
from dataclasses import replace
from decimal import Decimal

from freight_audit.audit import Invoice, expected_charge, money
from freight_audit.tariff import Tariff, TariffTable
from freight_audit.weight import DEFAULT_DIVISORS

LANES = ["GRU-MIA", "GRU-LIS", "GRU-FRA", "SAO-RIO", "SAO-CWB", "SAO-POA"]

# Four common billing faults.
ERROR_TYPES = ("wrong_divisor", "fuel_on_wrong_base", "wrong_break", "manual_surcharge")


def synthetic_tariffs() -> TariffTable:
    tariffs = []
    for lane in LANES:
        mode = "air" if lane.startswith("GRU") else "road"
        base = Decimal("4.80") if mode == "air" else Decimal("1.10")
        breaks = (
            (Decimal("0"), base),
            (Decimal("45"), money(base * Decimal("0.85"))),
            (Decimal("100"), money(base * Decimal("0.75"))),
            (Decimal("300"), money(base * Decimal("0.65"))),
        )
        tariffs.append(
            Tariff(
                lane=lane,
                mode=mode,
                breaks=breaks,
                minimum_charge=Decimal("75.00") if mode == "air" else Decimal("40.00"),
                fuel_surcharge_pct=Decimal("18.5") if mode == "air" else Decimal("12.0"),
                divisor_cm3_per_kg=DEFAULT_DIVISORS[mode],
            )
        )
    return TariffTable(tariffs)


def synthetic_invoices(
    n: int, table: TariffTable, seed: int = 42, error_rate: float = 0.12
) -> list[Invoice]:
    rng = random.Random(seed)
    out: list[Invoice] = []
    for k in range(n):
        t = rng.choice(table.all())
        dims = [Decimal(rng.randint(10, 120)) for _ in range(3)]
        actual = Decimal(rng.randint(5, 4000)) / Decimal(10)
        draft = Invoice(
            f"INV-{k:05d}",
            t.lane,
            t.mode,
            actual,
            dims[0],
            dims[1],
            dims[2],
            Decimal(0),
            Decimal(0),
        )
        exp = expected_charge(draft, table)
        freight, fuel = exp.freight, exp.fuel
        if rng.random() < error_rate:
            kind = rng.choice(ERROR_TYPES)
            if kind == "wrong_divisor":
                # smaller divisor means more volumetric kg
                bad = replace(t, divisor_cm3_per_kg=t.divisor_cm3_per_kg * Decimal("0.8"))
                exp_bad = expected_charge(draft, TariffTable([bad]))
                freight, fuel = exp_bad.freight, exp_bad.fuel
            elif kind == "fuel_on_wrong_base":
                fuel = money(fuel * Decimal("1.25"))
            elif kind == "wrong_break":
                freight = money(max(exp.chargeable_kg * t.breaks[0][1], t.minimum_charge))
                fuel = money(freight * t.fuel_surcharge_pct / 100)
            else:
                freight = money(freight + Decimal(rng.randint(5, 40)))
                fuel = money(freight * t.fuel_surcharge_pct / 100)
        out.append(replace(draft, billed_freight=freight, billed_fuel=fuel))
    return out
