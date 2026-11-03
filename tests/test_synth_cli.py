from pathlib import Path

import pytest

from freight_audit.audit import audit_all, summarize
from freight_audit.cli import main
from freight_audit.synth import synthetic_invoices, synthetic_tariffs


def test_generator_is_deterministic() -> None:
    t = synthetic_tariffs()
    assert synthetic_invoices(50, t, seed=7) == synthetic_invoices(50, t, seed=7)


def test_clean_data_has_no_findings() -> None:
    t = synthetic_tariffs()
    s = summarize(audit_all(synthetic_invoices(300, t, seed=1, error_rate=0.0), t))
    assert s.flagged_overcharges == 0 and s.flagged_undercharges == 0


def test_all_error_types_are_caught() -> None:
    t = synthetic_tariffs()
    s = summarize(audit_all(synthetic_invoices(400, t, seed=3, error_rate=1.0), t))
    assert s.flagged_overcharges > 300
    assert s.recoverable > 0


def test_cli_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["generate", "--out", str(tmp_path), "-n", "200", "--seed", "42"]) == 0
    report = tmp_path / "rep.csv"
    assert (
        main(
            [
                "audit",
                "--tariffs",
                str(tmp_path / "tariffs.csv"),
                "--invoices",
                str(tmp_path / "invoices.csv"),
                "--report",
                str(report),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "synthetic example data" in out
    assert report.exists()
