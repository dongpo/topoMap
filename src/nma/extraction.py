from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


CODE_PATTERN = re.compile(r"(?<!\d)(\d{7})(?!\d)")


def pdf_text(pdf: Path) -> str:
    """Extract layout-preserving PDF text with the open-source Poppler utility."""

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "document.txt"
        process = subprocess.run(
            ["pdftotext", "-layout", str(pdf), str(output)],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode:
            raise RuntimeError(f"pdftotext failed: {process.stderr.strip()}")
        return output.read_text(encoding="utf-8", errors="replace")


def extract_code_anchored_candidates(text: str, context_lines: int = 2) -> list[dict[str, Any]]:
    """Find candidate table records without pretending they are already trusted rules."""

    pages = text.split("\f")
    candidates: list[dict[str, Any]] = []
    for page_number, page in enumerate(pages, start=1):
        lines = page.splitlines()
        for index, line in enumerate(lines):
            codes = CODE_PATTERN.findall(line)
            for code in codes:
                start = max(0, index - context_lines)
                end = min(len(lines), index + context_lines + 1)
                candidates.append(
                    {
                        "feature_code": code,
                        "page": page_number,
                        "context": "\n".join(lines[start:end]).strip(),
                        "review_status": "candidate-not-executable",
                    }
                )
    return candidates


def extract_pdf_candidates(pdf: Path) -> list[dict[str, Any]]:
    return extract_code_anchored_candidates(pdf_text(pdf))


def write_jsonl(records: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
