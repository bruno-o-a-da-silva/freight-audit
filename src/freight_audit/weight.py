"""Chargeable-weight rules.

Volumetric weight converts a parcel's volume into an equivalent mass using a
divisor expressed in cm3/kg. The divisor is a contract assumption, not a law of
nature; the defaults below are common market conventions and must be checked
against each carrier agreement.
"""

from decimal import ROUND_CEILING, Decimal

# Assumed default divisors in cm3/kg (configurable per contract).
DEFAULT_DIVISORS: dict[str, Decimal] = {
    "air": Decimal("6000"),
    "express": Decimal("5000"),
    "road": Decimal("3000"),
}


def volumetric_weight_kg(
    length_cm: Decimal, width_cm: Decimal, height_cm: Decimal, divisor_cm3_per_kg: Decimal
) -> Decimal:
    """Return volumetric weight in kg: (L * W * H) [cm3] / divisor [cm3/kg]."""
    for value in (length_cm, width_cm, height_cm):
        if value <= 0:
            raise ValueError("dimensions must be positive")
    if divisor_cm3_per_kg <= 0:
        raise ValueError("divisor must be positive")
    return length_cm * width_cm * height_cm / divisor_cm3_per_kg


def round_up(value: Decimal, increment: Decimal) -> Decimal:
    """Round value up to the next multiple of increment (e.g. 0.5 kg)."""
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
    """Chargeable weight = max(actual, volumetric), rounded up to increment_kg."""
    if actual_kg <= 0:
        raise ValueError("actual weight must be positive")
    vol = volumetric_weight_kg(length_cm, width_cm, height_cm, divisor_cm3_per_kg)
    return round_up(max(actual_kg, vol), increment_kg)
