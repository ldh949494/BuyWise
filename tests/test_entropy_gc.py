from scripts.entropy_gc import render_deterministic_report


def test_entropy_gc_report_contains_cleanup_prompts() -> None:
    report = render_deterministic_report()

    assert "# Entropy GC Report" in report
    assert "## Cleanup Candidates" in report
    assert "ERROR:" in report
    assert "FIX:" in report
