# Why volumetric weight exists: a physics-grounded derivation

This note derives the chargeable-weight rule used by `freight_audit` from first
principles, states every unit and assumption, and validates the code against a
case computed by hand.

## 1. Quantities and units

| Symbol | Meaning | Unit |
|---|---|---|
| m | actual (gross) mass of a shipment | kg |
| L, W, H | outer dimensions of the shipment | cm |
| V = L·W·H | shipment volume | cm³ (1 m³ = 10⁶ cm³) |
| ρ = m / V | shipment density | kg/cm³ (often quoted in kg/m³) |
| M_max | payload mass limit of the vehicle or unit load device | kg |
| V_max | usable cargo volume of the vehicle | m³ |
| η | load factor: share of V_max that can actually be filled (0 < η ≤ 1) | dimensionless |
| ρ* | break-even (design) density of the vehicle | kg/m³ |
| D | volumetric divisor | cm³/kg |
| m_v = V / D | volumetric weight | kg |
| m_c | chargeable weight | kg |
| r | contracted rate for the applicable weight break | currency/kg |
| C_min | contracted minimum charge | currency |
| f | fuel surcharge | % of freight |

## 2. Two constraints on every vehicle

A truck, container or aircraft hold runs out of capacity in one of two ways:

1. **Mass**: the sum of shipment masses reaches the payload limit M_max
   (axle loads, structural limits, take-off weight).
2. **Volume**: the sum of shipment volumes reaches the usable space η·V_max
   (cargo cannot be stacked into every cubic centimetre, hence η < 1).

The density at which both limits are reached at the same time is

    ρ* = M_max / (η · V_max)            [kg / m³]

- If a shipment's density ρ > ρ*, the vehicle "weighs out": mass is the binding
  constraint, and charging per kilogram of actual mass recovers the cost of the
  capacity used.
- If ρ < ρ*, the vehicle "cubes out": it fills with volume while still below its
  mass limit. Charging per actual kilogram would undercharge light, bulky freight
  for the capacity it consumes.

## 3. From break-even density to the divisor

To price both cases on one scale, the carrier converts volume into an equivalent
mass at the break-even density:

    m_v = V · ρ*

With V in cm³ and ρ* in kg/m³, m_v = V · ρ* / 10⁶. Carriers publish the inverse
of ρ* in cm³/kg as the divisor:

    D = 10⁶ / ρ*                       [cm³ / kg]
    m_v = V / D                        [kg]

Common conventions (treated here as **configurable assumptions**, never as
universal facts; check each contract):

| Mode (assumption) | D [cm³/kg] | Implied ρ* [kg/m³] |
|---|---|---|
| Air cargo (widely used IATA convention) | 6000 | 166.7 |
| Express / courier (frequent convention) | 5000 | 200 |
| Road, some markets | 3000 | 333.3 |

Illustrative sanity check (assumed round numbers, not a specific vehicle): a
road vehicle with M_max = 24,000 kg, V_max = 90 m³ and η = 0.80 gives
ρ* = 24,000 / 72 ≈ 333 kg/m³, i.e. D ≈ 3000 cm³/kg, matching the road
convention above.

## 4. Chargeable weight and the charge

Because a shipment consumes whichever capacity binds first:

    m_c = ceil_Δ( max(m, V / D) )      [kg]

where ceil_Δ rounds up to the contract increment Δ (assumed 0.5 kg). Equivalently
m_c ≈ V · max(ρ, ρ*), which makes the physical meaning explicit.

The contracted charge is then

    freight = max(m_c · r(m_c), C_min)            [currency]
    fuel    = freight · f / 100                   [currency]
    total   = freight + fuel                      [currency]

where r(m_c) is the rate of the highest weight break whose lower bound is
≤ m_c. Money is computed with `decimal.Decimal` and rounded half-up to cents.

### Stated assumptions

1. Divisor is per tariff (lane and mode) and defaults to the table above.
2. Weight increment Δ = 0.5 kg, rounding up.
3. Weight breaks apply the single break rate to the whole chargeable weight
   (no "break-point" or blended pricing).
4. Fuel surcharge is a percentage of the freight after the minimum charge.
5. Accessorials (handling, security, dangerous goods) are out of scope.
6. Tolerance for a discrepancy is 0.01 currency units.

## 5. Validation against a hand-computed case

Shipment: air, lane GRU-MIA, m = 12.3 kg, 60 × 50 × 40 cm.
Tariff (synthetic): breaks 0 kg → 4.80, 45 kg → 4.08, 100 kg → 3.60 per kg;
C_min = 75.00; f = 18.5 %; D = 6000 cm³/kg.

1. V = 60 · 50 · 40 = 120,000 cm³
2. m_v = 120,000 / 6000 = 20.0 kg
3. ρ = 12.3 kg / 0.12 m³ = 102.5 kg/m³ < ρ* = 166.7 kg/m³, so the shipment cubes out
4. m_c = ceil_0.5(max(12.3, 20.0)) = 20.0 kg
5. r(20.0) = 4.80 (below the 45 kg break)
6. freight = max(20.0 · 4.80, 75.00) = 96.00
7. fuel = 96.00 · 0.185 = 17.76
8. total = 113.76

If the carrier billed with D = 5000 instead (m_v = 24.0 kg): freight 115.20,
fuel 21.31, total 136.51, so the overcharge is 22.75. Both numbers are asserted
in `tests/test_audit.py` (`test_hand_computed_case`,
`test_overcharge_on_actual_weight_divisor_error`).
