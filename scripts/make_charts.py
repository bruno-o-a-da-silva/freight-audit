"""Redraw docs/img charts from the seeded generator (seed 42, n=2000). Needs matplotlib."""

from collections import defaultdict
from decimal import Decimal

import matplotlib.pyplot as plt
from _style import BG, GOLD, GOLD_DIM, IMG, MUTED, TEXT, style, title

from freight_audit.audit import audit_all, summarize
from freight_audit.synth import synthetic_invoices, synthetic_tariffs


def main() -> None:
    style()
    table = synthetic_tariffs()
    findings = audit_all(synthetic_invoices(2000, table, seed=42), table)
    s = summarize(findings)
    by_lane: dict[str, Decimal] = defaultdict(Decimal)
    for f in findings:
        if f.status == "overcharge":
            by_lane[f.invoice.lane] += f.difference
    lanes = sorted(by_lane, key=lambda x: by_lane[x], reverse=True)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    vals = [float(by_lane[x]) for x in lanes]
    bars = ax.bar(lanes, vals, color=GOLD_DIM, width=0.62)
    bars[0].set_color(GOLD)
    for b, v in zip(bars, vals, strict=True):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v,
            f"{v:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=TEXT,
        )
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Overcharge")
    title(
        ax,
        "Recoverable overcharge by lane",
        f"Total {s.recoverable:,.2f} across {len(findings):,} invoices",
    )
    fig.tight_layout()
    fig.savefig(IMG / "overcharge_by_lane.png")
    plt.close(fig)

    diffs = [float(f.difference) for f in findings if f.status != "ok"]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.hist(diffs, bins=30, color=GOLD, edgecolor=BG, linewidth=0.8)
    ax.axvline(0, color=MUTED, lw=1, ls="--")
    ax.grid(axis="x", visible=False)
    title(ax, "Billed minus expected", f"{len(diffs)} flagged invoices")
    ax.set_xlabel("Difference per invoice")
    ax.set_ylabel("Invoices")
    fig.tight_layout()
    fig.savefig(IMG / "difference_histogram.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
