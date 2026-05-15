import pytest

from scripts.ai_update_readme import replace_auto_docs_block


def test_replace_auto_docs_block_only_updates_marked_region() -> None:
    readme = """# Project

Manual intro.

<!-- AUTO-DOCS:START -->

Old generated content.

<!-- AUTO-DOCS:END -->

Manual footer.
"""

    updated = replace_auto_docs_block(readme, "New generated content.")

    assert "Manual intro." in updated
    assert "Manual footer." in updated
    assert "Old generated content." not in updated
    assert "New generated content." in updated
    assert updated.count("<!-- AUTO-DOCS:START -->") == 1
    assert updated.count("<!-- AUTO-DOCS:END -->") == 1


def test_replace_auto_docs_block_requires_markers() -> None:
    with pytest.raises(ValueError, match="AUTO-DOCS"):
        replace_auto_docs_block("# Project\n", "Generated content.")
