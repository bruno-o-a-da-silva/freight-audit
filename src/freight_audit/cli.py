"""Command-line interface: generate synthetic data and run an audit."""

import argparse
from pathlib import Path

from freight_audit.audit import audit_all, load_invoices, summarize, write_invoices, write_report
from freight_audit.synth import synthetic_invoices, synthetic_tariffs
from freight_audit.tariff import load_tariffs, write_tariffs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="freight-audit", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="write synthetic tariffs.csv and invoices.csv")
    g.add_argument("--out", type=Path, default=Path("data"))
    g.add_argument("-n", type=int, default=2000)
    g.add_argument("--seed", type=int, default=42)
    a = sub.add_parser("audit", help="audit invoices against tariffs")
    a.add_argument("--tariffs", type=Path, required=True)
    a.add_argument("--invoices", type=Path, required=True)
    a.add_argument("--report", type=Path, default=Path("discrepancies.csv"))
    args = p.parse_args(argv)

    if args.cmd == "generate":
        args.out.mkdir(parents=True, exist_ok=True)
        table = synthetic_tariffs()
        write_tariffs(table, args.out / "tariffs.csv")
        write_invoices(synthetic_invoices(args.n, table, args.seed), args.out / "invoices.csv")
        print(f"wrote {args.out / 'tariffs.csv'} and {args.out / 'invoices.csv'}")
        return 0

    table = load_tariffs(args.tariffs)
    findings = audit_all(load_invoices(args.invoices), table)
    write_report([f for f in findings if f.status != "ok"], args.report)
    print("Freight audit summary (synthetic example data)")
    for line in summarize(findings).lines():
        print(line)
    print(f"Discrepancy report: {args.report}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
