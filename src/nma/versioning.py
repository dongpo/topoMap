from __future__ import annotations

from typing import Any

from .specification import Specification


def compare_specifications(old: Specification, new: Specification) -> dict[str, Any]:
    old_rules = {rule.rule_id: rule for rule in old.rules}
    new_rules = {rule.rule_id: rule for rule in new.rules}
    common = old_rules.keys() & new_rules.keys()
    return {
        "from_version": old.version,
        "to_version": new.version,
        "added_rules": sorted(new_rules.keys() - old_rules.keys()),
        "removed_rules": sorted(old_rules.keys() - new_rules.keys()),
        "changed_constraints": sorted(
            rule_id
            for rule_id in common
            if old_rules[rule_id].constraint != new_rules[rule_id].constraint
        ),
    }
