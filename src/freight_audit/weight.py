"""Chargeable weight. The divisor (cm3/kg) comes from the contract, not physics;
the defaults are the usual market values. See docs/derivation.md."""

from decimal import ROUND_CEILING, Decimal

DEFAULT_DIVISORS: dict[str, Decimal] = {
    "air": Decimal("6000"),
    "express": Decimal("5000"),
    "road": Decimal("3000"),
}


def volumetric_weight_kg(
    length_cm: Decimal, width_cm: Decimal, height_cm: Decimal, divisor_cm3_per_kg: Decimal
) -> Decimal:
    for value in (length_cm, width_cm, height_cm):
        if value <= 0:
            raise ValueError("dimensions must be positive")
    if divisor_cm3_per_kg <= 0:
        raise ValueError("divisor must be positive")
    return length_cm * width_cm * height_cm / divisor_cm3_per_kg


def round_up(value: Decimal, increment: Decimal) -> Decimal:
    if increment <= 0:
        raise ValueError("increment must be positive")
    return (value / increment).to_integral_value(rounding=ROUND_CEILING) * increment


def chargeable_weight_kg(
    actual_kg: Decimal,
    length_cm: Decimal,
    width_cm: Decimal,
    height_cm: Decimal,
    divisor_cm3_per_kg: Decimal,
    increment_kg: Decimal = Decimal("0.5"),
) -> Decimal:
    # Carriers round up, never to nearest: 20.01 kg bills as 20.5.
    if actual_kg <= 0:
        raise ValueError("actual weight must be positive")
    vol = volumetric_weight_kg(length_cm, width_cm, height_cm, divisor_cm3_per_kg)
    return round_up(max(actual_kg, vol), increment_kg)
