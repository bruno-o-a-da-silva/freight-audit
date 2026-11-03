"""Draw docs/img/hero.png (1600x640): a parcel and its volumetric vs actual weight crossover.

The parcel is the first air invoice of the seeded generator (seed 42) whose volumetric
weight exceeds its actual weight; every number is computed by the library.
"""

from decimal import Decimal

import matplotlib.pyplot as plt
from _style import BG, GOLD, GOLD_DIM, IMG, LINE, MUTED, SERIF, TEXT, style

from freight_audit.synth import synthetic_invoices, synthetic_tariffs
from freight_audit.weight import chargeable_weight_kg, volumetric_weight_kg


def main() -> None:
    style()
    table = synthetic_tariffs()
    inv = next(
        i for i in synthetic_invoices(2000, table, seed=42)
        if i.mode == "air" and volumetric_weight_kg(
            i.length_cm, i.width_cm, i.height_cm, table.lookup(i.lane, i.mode).divisor_cm3_per_kg
        ) > i.actual_kg
    )
    div = table.lookup(inv.lane, inv.mode).divisor_cm3_per_kg
    L, W, H = inv.length_cm, inv.width_cm, inv.height_cm
    vol = volumetric_weight_kg(L, W, H, div)
    charged = chargeable_weight_kg(inv.actual_kg, L, W, H, div)

    fig = plt.figure(figsize=(16, 6.4), dpi=100)
    fig.text(0.05, 0.70, "freight-audit", fontfamily=SERIF, fontsize=50, color=TEXT)
    fig.text(0.05, 0.60, "Recompute every freight invoice from the contract.",
             fontsize=17, color=TEXT)
    fig.text(0.05, 0.545, "Flag the ones that do not match.", fontsize=17, color=MUTED)
    fig.add_artist(plt.Line2D([0.05, 0.12], [0.47, 0.47], color=GOLD, lw=2))
    fig.text(0.05, 0.38, "chargeable = max(actual, L\u00b7W\u00b7H / divisor)",
             fontsize=14, color=GOLD, fontfamily="DejaVu Sans Mono")
    fig.text(0.05, 0.32, f"{inv.invoice_id}  \u00b7  {inv.lane} air  \u00b7  divisor {div:.0f}",
             fontsize=12, color=MUTED)

    # Parcel, oblique projection
    ax = fig.add_axes((0.42, 0.12, 0.2, 0.76))
    ax.set_axis_off()
    ax.set_aspect("equal")
    lf, wf, hf = float(L), float(W), float(H)
    dx, dy = 0.5 * wf, 0.35 * wf
    front = [(0, 0), (lf, 0), (lf, hf), (0, hf)]
    top = [(0, hf), (lf, hf), (lf + dx, hf + dy), (dx, hf + dy)]
    side = [(lf, 0), (lf + dx, dy), (lf + dx, hf + dy), (lf, hf)]
    for poly, fc in ((front, "#1A1A1A"), (top, "#232323"), (side, "#171717")):
        ax.add_patch(plt.Polygon(poly, closed=True, fc=fc, ec=GOLD, lw=1.6))
    ax.plot([lf / 2, lf / 2], [0, hf], color=GOLD_DIM, lw=0.8, ls=":")
    kw = {"color": TEXT, "fontsize": 12, "ha": "center", "va": "center"}
    ax.text(lf / 2, -0.12 * hf - 6, f"L {L:.0f} cm", **kw)
    ax.text(-10, hf / 2, f"H {H:.0f} cm", rotation=90, **kw)
    ax.text(lf + dx / 2 + 9, dy / 2 - 9, f"W {W:.0f} cm", rotation=35, **kw)
    ax.set_xlim(-22, lf + dx + 30)
    ax.set_ylim(-0.12 * hf - 14, hf + dy + 26)

    # Crossover curve
    cx = fig.add_axes((0.69, 0.2, 0.27, 0.62))
    v = float(vol)
    xs = [v * 2 * k / 400 for k in range(1, 401)]
    ys = [float(chargeable_weight_kg(Decimal(str(round(x, 3))), L, W, H, div)) for x in xs]
    cx.plot(xs, xs, color=MUTED, lw=1, ls="--")
    cx.axhline(v, color=MUTED, lw=1, ls="--")
    cx.plot(xs, ys, color=GOLD, lw=2.2)
    cx.scatter([v], [v], s=40, color=BG, edgecolor=GOLD, zorder=4, lw=1.5)
    cx.scatter([float(inv.actual_kg)], [float(charged)], s=46, color=GOLD, zorder=5)
    cx.annotate(f"billed as {charged} kg", (float(inv.actual_kg), float(charged)),
                xytext=(0, 14), textcoords="offset points", color=TEXT, fontsize=11)
    cx.text(v * 1.03, v * 0.84, f"crossover {v:.1f} kg", color=MUTED, fontsize=10)
    cx.text(v * 1.62, v * 1.82, "actual", color=MUTED, fontsize=10, ha="right")
    cx.text(v * 0.04, v * 1.1, "volumetric", color=MUTED, fontsize=10)
    cx.set_xlim(0, v * 2)
    cx.set_ylim(0, v * 2)
    cx.set_xlabel("Actual weight (kg)")
    cx.set_ylabel("Chargeable weight (kg)")
    cx.grid(color=LINE)
    fig.savefig(IMG / "hero.png", dpi=100)


if __name__ == "__main__":
    main()
