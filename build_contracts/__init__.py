"""BUILD-owned, non-executing entry contracts."""

from build_contracts.feature_profile import build_feature_profile
from build_contracts.fixture import (
    BuildFixtureError,
    fixture_identity,
    load_build_fixture_manifest,
    validate_build_fixture_manifest,
)
from build_contracts.resolution import (
    BuildResolutionError,
    inspect_private_build_source,
    load_build_source_observation,
    resolve_build_request,
    validate_build_source_observation,
)
from build_contracts.portrayal_decision import (
    BuildPortrayalDecisionError,
    prepare_build_portrayal,
    validate_decision,
    validate_portrayal_evidence,
    validate_proposal,
)
from build_contracts.gate_review import (
    BuildGateReviewError,
    prepare_build_gate_review,
    request_build_execution_authorization,
    validate_gate_review,
)

__all__ = [
    "BuildFixtureError",
    "BuildResolutionError",
    "BuildPortrayalDecisionError",
    "BuildGateReviewError",
    "build_feature_profile",
    "fixture_identity",
    "inspect_private_build_source",
    "load_build_fixture_manifest",
    "load_build_source_observation",
    "prepare_build_portrayal",
    "prepare_build_gate_review",
    "request_build_execution_authorization",
    "resolve_build_request",
    "validate_build_fixture_manifest",
    "validate_build_source_observation",
    "validate_decision",
    "validate_gate_review",
    "validate_portrayal_evidence",
    "validate_proposal",
]
