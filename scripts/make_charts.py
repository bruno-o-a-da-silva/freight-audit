"""Render docs/ charts from the seeded synthetic dataset (requires matplotlib)."""

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from freight_audit.audit import audit_all, summarize  # noqa: E402
from freight_audit.synth import synthetic_invoices, synthetic_tariffs  # noqa: E402

INDIGO, INDIGO_MID, INDIGO_LIGHT = "#3A2FD0", "#6E66F0", "#8F89FF"
PINK, PINK_TEXT = "#FF2E88", "#D81B6E"
DOCS = Path(__file__).resolve().parent.parent / "docs"


def style() -> None:
    for f in font_manager.findSystemFonts():
        if any(n in f for n in ("Playfair", "Inter", "IBMPlexMono")):
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({
        "font.family": "Inter", "axes.edgecolor": "#C9C6F5", "axes.labelcolor": "#1B1650",
        "xtick.color": "#1B1650", "ytick.color": "#1B1650", "axes.spines.top": False,
        "axes.spines.right": False, "figure.dpi": 150,
    })


def title(ax: plt.Axes, text: str) -> None:
    ax.set_title(text, fontfamily="Playfair Display", fontsize=15, color=INDIGO, loc="left")


def main() -> None:
    style()
    table = synthetic_tariffs()
    findings = audit_all(synthetic_invoices(2000, table, seed=42), table)
    s = summarize(findings)
    by_lane: dict[str, Decimal] = defaultdict(Decimal)
    for f in findings:
        if f.status == "overcharge":
            by_lane[f.invoice.lane] += f.difference
    lanes = sorted(by_lane)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.bar(lanes, [float(by_lane[x]) for x in lanes], color=INDIGO_MID)
    bars[max(range(len(lanes)), key=lambda i: by_lane[lanes[i]])].set_color(INDIGO)
    title(ax, "Recoverable overcharge by lane")
    ax.set_ylabel("Overcharge (currency units)")
    ax.text(0.99, 0.97, f"total {s.recoverable:,.2f}", transform=ax.transAxes, ha="right",
            va="top", color=PINK_TEXT, fontfamily="IBM Plex Mono", fontsize=10)
    fig.text(0.01, 0.01, "synthetic example data, seed 42, n=2000", fontsize=8,
             color="#6B679A", fontfamily="IBM Plex Mono")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(DOCS / "overcharge_by_lane.png")

    diffs = [float(f.difference) for f in findings if f.status != "ok"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.hist(diffs, bins=30, color=INDIGO_LIGHT, edgecolor=INDIGO)
    ax.axvline(0, color=PINK, lw=1.5)
    title(ax, "Billed minus expected, flagged invoices")
    ax.set_xlabel("Difference per invoice (currency units)")
    ax.set_ylabel("Invoices")
    fig.text(0.01, 0.01, "synthetic example data, seed 42, n=2000", fontsize=8,
             color="#6B679A", fontfamily="IBM Plex Mono")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(DOCS / "difference_histogram.png")


if __name__ == "__main__":
    main()
