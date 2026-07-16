from pathlib import Path

from nma.specification import Specification
from nma.versioning import compare_specifications

ROOT = Path(__file__).resolve().parents[1]


def test_version_changes_are_machine_detectable() -> None:
    old = Specification.load(ROOT / "data/specifications/tnm-demo-2023.json")
    new = Specification.load(ROOT / "data/specifications/tnm-demo-2024.json")
    assert compare_specifications(old, new) == {
        "from_version": "2023",
        "to_version": "2024",
        "added_rules": ["NMA-SCHEMA-003"],
        "removed_rules": [],
        "changed_constraints": ["NMA-DOMAIN-001"],
    }
