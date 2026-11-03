from decimal import Decimal as D
from pathlib import Path

import pytest

from freight_audit.tariff import Tariff, TariffTable, load_tariffs, write_tariffs


def test_rate_for_picks_highest_applicable_break(table: TariffTable) -> None:
    t = table.lookup("GRU-MIA", "air")
    assert t.rate_for(D(20)) == D("4.80")
    assert t.rate_for(D(45)) == D("4.08")
    assert t.rate_for(D(500)) == D("3.60")


def test_rate_for_without_covering_break() -> None:
    t = Tariff("X", "air", ((D(10), D(1)),), D(0), D(0), D(6000))
    with pytest.raises(ValueError):
        t.rate_for(D(5))


def test_lookup_missing_lane(table: TariffTable) -> None:
    with pytest.raises(KeyError):
        table.lookup("GRU-XXX", "air")


def test_duplicate_tariff_rejected(table: TariffTable) -> None:
    t = table.lookup("GRU-MIA", "air")
    with pytest.raises(ValueError):
        TariffTable([t, t])


def test_roundtrip_csv(table: TariffTable, tmp_path: Path) -> None:
    path = tmp_path / "t.csv"
    write_tariffs(table, path)
    loaded = load_tariffs(path)
    assert len(loaded) == 1
    assert loaded.lookup("GRU-MIA", "air") == table.lookup("GRU-MIA", "air")


def test_missing_divisor_uses_mode_default(tmp_path: Path) -> None:
    path = tmp_path / "t.csv"
    path.write_text(
        "lane,mode,min_kg,rate_per_kg,minimum_charge,fuel_pct,divisor\nSAO-RIO,road,0,1.10,40,12,\n"
    )
    assert load_tariffs(path).lookup("SAO-RIO", "road").divisor_cm3_per_kg == D(3000)
