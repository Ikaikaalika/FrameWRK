from pathlib import Path

from scripts.generate_docs import generate_docs


def test_generate_docs(tmp_path: Path):
    output_dir = tmp_path / "docs"
    generate_docs(output_dir, count=3)
    files = sorted(output_dir.glob("*.md"))
    assert len(files) == 3
    content = files[0].read_text(encoding="utf-8")
    assert content.startswith("Title:")
    assert "Automation Ideas" in content
