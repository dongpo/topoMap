import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_local_markdown_links_resolve() -> None:
    markdown_files = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    missing: list[str] = []
    for source in markdown_files:
        text = source.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if path and not (source.parent / path).resolve().exists():
                missing.append(f"{source.relative_to(ROOT)} -> {target}")
    assert not missing, "Missing local documentation links:\n" + "\n".join(missing)
