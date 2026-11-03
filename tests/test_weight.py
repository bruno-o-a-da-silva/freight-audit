from decimal import Decimal as D

import pytest

from freight_audit.weight import chargeable_weight_kg, round_up, volumetric_weight_kg


def test_volumetric_air_known_case() -> None:
    # 60 x 50 x 40 cm = 120,000 cm3 / 6000 cm3/kg = 20 kg
    assert volumetric_weight_kg(D(60), D(50), D(40), D(6000)) == D(20)


def test_chargeable_takes_volumetric_when_light_bulky() -> None:
    assert chargeable_weight_kg(D("12.3"), D(60), D(50), D(40), D(6000)) == D("20.0")


def test_chargeable_takes_actual_when_dense_and_rounds_up() -> None:
    assert chargeable_weight_kg(D("20.1"), D(10), D(10), D(10), D(6000)) == D("20.5")


def test_road_divisor_doubles_volumetric() -> None:
    assert volumetric_weight_kg(D(60), D(50), D(40), D(3000)) == D(40)


def test_round_up_exact_multiple() -> None:
    assert round_up(D("2.0"), D("0.5")) == D("2.0")


@pytest.mark.parametrize(
    "args",
    [(D(0), D(1), D(1), D(6000)), (D(1), D(1), D(1), D(0))],
)
def test_volumetric_rejects_bad_input(args: tuple[D, D, D, D]) -> None:
    with pytest.raises(ValueError):
        volumetric_weight_kg(*args)


def test_round_up_rejects_bad_increment() -> None:
    with pytest.raises(ValueError):
        round_up(D(1), D(0))


def test_chargeable_rejects_nonpositive_weight() -> None:
    with pytest.raises(ValueError):
        chargeable_weight_kg(D(0), D(1), D(1), D(1), D(6000))
