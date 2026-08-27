from copy import deepcopy
from datetime import datetime, timezone

import pytest

from hero04_support import make_authorization
from nma.school_hero_execution import (
    ExecutionAuthorizationVerifier,
    SchoolHeroExecutionError,
    authorization_sha256,
)


def NOW() -> datetime:
    return datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def verifier() -> ExecutionAuthorizationVerifier:
    return ExecutionAuthorizationVerifier(now=NOW)


def rehash(value: dict) -> dict:
    value["authorization_hash"] = authorization_sha256(value)
    return value


def test_valid_complete_authorization() -> None:
    result = verifier().verify(make_authorization())
    assert result["schema"] == "nma.symbol-edit-authorization/1.0"
    assert result["feature_identity"] == {"code": "9920103", "geometry_role": "Point"}


def test_missing_authorization_and_bare_approval_are_rejected() -> None:
    with pytest.raises(SchoolHeroExecutionError, match="complete HERO-03"):
        verifier().verify(None)
    with pytest.raises(SchoolHeroExecutionError, match="complete HERO-03"):
        verifier().verify({"proposal_id": "x", "decision": "approved"})


def test_rejected_and_expired_authorization_are_rejected() -> None:
    rejected = rehash({**make_authorization(), "status": "rejected"})
    with pytest.raises(SchoolHeroExecutionError, match="not ready"):
        verifier().verify(rejected)
    expired = rehash({**make_authorization(), "expires_at": "2026-08-14T11:59:59Z"})
    with pytest.raises(SchoolHeroExecutionError, match="expired"):
        verifier().verify(expired)


def test_authorization_and_proposal_hash_mismatch_are_rejected() -> None:
    authorization = make_authorization()
    authorization["authorization_hash"] = "f" * 64
    with pytest.raises(SchoolHeroExecutionError, match="authorization hash"):
        verifier().verify(authorization)
    proposal = make_authorization()
    proposal["proposal_payload"]["operations"][0]["value"]["color"] = "#c62828"
    rehash(proposal)
    with pytest.raises(SchoolHeroExecutionError, match="proposal hash"):
        verifier().verify(proposal)


def test_scope_validation_and_identity_binding() -> None:
    scoped = make_authorization(scope=["derived-real-layer"])
    with pytest.raises(SchoolHeroExecutionError, match="scope"):
        verifier().verify(scoped)
    changed = deepcopy(make_authorization())
    changed["human_approval"]["proposal_revision"] = 5
    rehash(changed)
    with pytest.raises(SchoolHeroExecutionError, match="approval identity"):
        verifier().verify(changed)
