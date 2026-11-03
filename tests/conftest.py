from decimal import Decimal as D

import pytest

from freight_audit.audit import Invoice
from freight_audit.tariff import Tariff, TariffTable


@pytest.fixture
def table() -> TariffTable:
    return TariffTable(
        [
            Tariff(
                lane="GRU-MIA",
                mode="air",
                breaks=((D(0), D("4.80")), (D(45), D("4.08")), (D(100), D("3.60"))),
                minimum_charge=D("75.00"),
                fuel_surcharge_pct=D("18.5"),
                divisor_cm3_per_kg=D(6000),
            )
        ]
    )


def make_invoice(
    freight: str, fuel: str, actual: str = "12.3", dims: tuple[str, str, str] = ("60", "50", "40")
) -> Invoice:
    # Default is the carton from docs/derivation.md section 5.
    length, width, height = (D(x) for x in dims)
    return Invoice(
        "AWB 047-31884215", "GRU-MIA", "air", D(actual), length, width, height, D(freight), D(fuel)
    )
