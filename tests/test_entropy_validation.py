import ast

from scripts.validate_entropy import (
    EntropyIssue,
    ROOT,
    check_function_lengths,
    check_todo_lines,
)


def test_entropy_issue_render_includes_error_fix_and_see() -> None:
    issue = EntropyIssue(
        rule="function-length",
        path="app/services/example.py",
        line=10,
        symbol="handle_example",
        detail="Function exceeds 30 lines limit; found 45.",
        fix="Split orchestration into smaller helpers.",
        see="docs/conventions/golden-principles.md",
    )

    rendered = issue.render()

    assert "app/services/example.py:10" in rendered
    assert "ERROR: Function exceeds 30 lines limit; found 45." in rendered
    assert "FIX: Split orchestration into smaller helpers." in rendered
    assert "SEE: docs/conventions/golden-principles.md" in rendered


def test_function_length_check_reports_long_function() -> None:
    body = "\n".join(f"    value_{index} = {index}" for index in range(31))
    tree = ast.parse(f"def handle_example():\n{body}\n    return value_30\n")
    issues = []

    check_function_lengths(ROOT / "app" / "services" / "example.py", tree, issues)

    assert len(issues) == 1
    assert issues[0].rule == "function-length"
    assert "FIX:" in issues[0].render()


def test_todo_check_requires_owner_or_issue() -> None:
    issues = []
    path = ROOT / "app" / "services" / "example.py"

    check_todo_lines(path, ["# TODO: clean this later", "# TODO owner: alice"], issues)

    assert len(issues) == 1
    assert issues[0].rule == "bare-todo"
