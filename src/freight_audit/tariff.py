"""Contracted tariff tables with weight breaks."""

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from freight_audit.weight import DEFAULT_DIVISORS


@dataclass(frozen=True)
class Tariff:
    # breaks: ascending (min_kg, rate_per_kg). The highest break reached prices the
    # whole weight; no blended or break-point pricing.

    lane: str
    mode: str
    breaks: tuple[tuple[Decimal, Decimal], ...]
    minimum_charge: Decimal
    fuel_surcharge_pct: Decimal
    divisor_cm3_per_kg: Decimal

    def rate_for(self, chargeable_kg: Decimal) -> Decimal:
        applicable = [rate for min_kg, rate in self.breaks if chargeable_kg >= min_kg]
        if not applicable:
            raise ValueError(f"no weight break covers {chargeable_kg} kg on {self.lane}")
        return applicable[-1]


class TariffTable:
    def __init__(self, tariffs: list[Tariff]) -> None:
        self._by_key: dict[tuple[str, str], Tariff] = {}
        for t in tariffs:
            key = (t.lane, t.mode)
            if key in self._by_key:
                raise ValueError(f"duplicate tariff for {key}")
            self._by_key[key] = t

    def lookup(self, lane: str, mode: str) -> Tariff:
        try:
            return self._by_key[(lane, mode)]
        except KeyError:
            raise KeyError(f"no contracted tariff for lane={lane} mode={mode}") from None

    def __len__(self) -> int:
        return len(self._by_key)

    def all(self) -> list[Tariff]:
        return list(self._by_key.values())


TARIFF_FIELDS = ["lane", "mode", "min_kg", "rate_per_kg", "minimum_charge", "fuel_pct", "divisor"]


def load_tariffs(path: Path) -> TariffTable:
    # One row per weight break; minimum, fuel and divisor are read from the first row.
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            grouped.setdefault((row["lane"], row["mode"]), []).append(row)
    tariffs = []
    for (lane, mode), rows in grouped.items():
        first = rows[0]
        divisor = first.get("divisor") or str(DEFAULT_DIVISORS[mode])
        breaks = sorted((Decimal(r["min_kg"]), Decimal(r["rate_per_kg"])) for r in rows)
        tariffs.append(
            Tariff(
                lane=lane,
                mode=mode,
                breaks=tuple(breaks),
                minimum_charge=Decimal(first["minimum_charge"]),
                fuel_surcharge_pct=Decimal(first["fuel_pct"]),
                divisor_cm3_per_kg=Decimal(divisor),
            )
        )
    return TariffTable(tariffs)


def write_tariffs(table: TariffTable, path: Path) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(TARIFF_FIELDS)
        for t in table.all():
            for min_kg, rate in t.breaks:
                w.writerow(
                    [
                        t.lane,
                        t.mode,
                        min_kg,
                        rate,
                        t.minimum_charge,
                        t.fuel_surcharge_pct,
                        t.divisor_cm3_per_kg,
                    ]
                )
