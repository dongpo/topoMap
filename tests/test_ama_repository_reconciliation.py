from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN_TAGS = {
    "nma-road-v1.0-final": (
        "d60fffa873428d1ba8b308ea0d4d2028ac8431fd",
        "325c70d5335f57c43a8af85822db25032aa225c3",
    ),
    "nma-core-v1.0-final": (
        "5729f2db0fc441b3eb0a22c1f76b0f6af3f368ea",
        "5eb138ae7686502431587743ebce9ddf92c5a799",
    ),
    "nma-build-v1.0-final": (
        "1b55ff67fd670a482da74975ce41fa86df5dd71f",
        "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7",
    ),
    "nma-generalization-v1.0-final": (
        "9ba26ff032e23f0ba5de80d809f08eb6e973bb4f",
        "380cc6ea2a4498ce83690521c933accfd918818e",
    ),
    "nma-demo-v1.0-final": (
        "794a71ab8fdf56c4504f85521f7a063a9acb63f9",
        "05af154a14e781f20b5cf2d3996eac8191875b0f",
    ),
    "nma-v1.0-final": (
        "f710da4828cd9ebf170fb60bd6af8f81e4e7abff",
        "eb87bde775333811529efb6f651573ea21cf456b",
    ),
}


def _git(*arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_frozen_annotated_tag_objects_and_targets_are_exact() -> None:
    for tag, (tag_object, peeled_target) in FROZEN_TAGS.items():
        assert _git("cat-file", "-t", f"refs/tags/{tag}") == "tag"
        assert _git("rev-parse", f"refs/tags/{tag}") == tag_object
        assert _git("rev-parse", f"refs/tags/{tag}^{{}}") == peeled_target


def test_reconciliation_contains_both_canonical_histories() -> None:
    for ancestor in (
        "eb87bde775333811529efb6f651573ea21cf456b",
        "0620e75705338f2096a7c9ef9a1f2de185a46577",
        "00252f32647be08476157237d8025dad9b062ed1",
    ):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, "HEAD"],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0, ancestor


def test_frozen_root_report_bytes_are_unchanged() -> None:
    report_names = [
        path
        for path in _git("ls-tree", "-r", "--name-only", "nma-v1.0-final^{}").splitlines()
        if "/" not in path and path.endswith(("-Report.md", "-Audit.md"))
    ]
    assert report_names
    for path in report_names:
        snapshot = subprocess.run(
            ["git", "show", f"nma-v1.0-final^{{}}:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert (ROOT / path).read_bytes() == snapshot, path


def test_version_and_compatibility_namespaces_are_explicit() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    policy = (ROOT / "docs/open-source/VERSIONING.md").read_text(encoding="utf-8")

    assert 'name = "national-map-agent"' in pyproject
    assert 'version = "0.2.0"' in pyproject
    assert 'nma = "nma.cli:main"' in pyproject
    assert 'nma-bench = "nma.portrayal_bench:main"' in pyproject
    assert "Authoritative Mapping Agent (AMA)" in citation
    assert "version: 0.2.0" in citation
    assert "No `ama-v1.0` tag is created" in policy
    assert not [tag for tag in _git("tag", "--list", "ama-*").splitlines() if tag]


def test_pages_is_an_explicit_artifact_not_the_repository_root() -> None:
    workflow = (ROOT / ".github/workflows/static.yml").read_text(encoding="utf-8")
    assert "test_gh_pages_static_demo.py" in workflow
    assert "path: public/gh-pages" in workflow
    assert "path: '.'" not in workflow
    assert (ROOT / "public/gh-pages/index.html").is_file()
    assert (ROOT / "src/nma").is_dir()
