from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, FormatChecker
import pytest

from nma.real_layer import REAL_LAYER_PROFILES
from nma.road_approval import authorization_sha256
from nma.road_execution import (
    FrozenRoadAuthorizationVerifier,
    FrozenRoadInputs,
    RoadAuthorizationStore,
    RoadExecutionError,
)


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "data/demo/public-demo-data-authority-matrix-v1.0.json"
SCHEMA_PATH = ROOT / "schemas/public-demo-data-authority-matrix-v1.0.schema.json"
PRIVATE_ARCHIVE = "data/datasets/112年多維度SHP成果_0502.zip"
PUBLISHABLE = {
    "REDISTRIBUTION_EXPLICITLY_ALLOWED",
    "REDISTRIBUTION_ALLOWED_WITH_ATTRIBUTION",
    "DERIVED_DATA_ALLOWED",
}
FROZEN_FILE_SHA256 = {
    "src/nma/real_layer.py": "d9eb720b5f84c35b63df8c9cd828a7530497d4b71f502117bdf7470148d890e9",
    "src/nma/school_hero_execution.py": (
        "91b70e0462d8144f1bed36f781d77b859fa9c407545b1b321c087ddf228a2f3c"
    ),
    "src/nma/road_execution.py": (
        "45e363ee32ed7fffd06d72df3be7577a9d404461c061f225780f1b9d84bc5883"
    ),
    "src/nma/road_approval.py": (
        "1d8ed41622d744a72620499daffda168907742655ec7fe5b6f8a726918581319"
    ),
    "schemas/road-execution-authorization-v1.0.schema.json": (
        "f8328d3a479948f0ef59221dbb63910efa7629056ec65f1bf4087ca5beebffdc"
    ),
    "data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json": (
        "ba010892193145cad8f6ee8d3331824f3a972cdb422ca902e6bd9c04801e9283"
    ),
    "data/specifications/nma-gen-02-road-contract-conformance-v1.0.json": (
        "eb15a4df83517af0e7b069cb0411f05941b3cbc9e02a88b6dfc6487b14ab3091"
    ),
    "data/specifications/nma-gen-02-school-hero-contract-conformance-v1.0.json": (
        "8c4a44a30b104c399fa596ef3ddafb37bc0ff607d57337a6a03f3520e70c262e"
    ),
}


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _matrix_sha256(matrix: dict[str, object]) -> str:
    basis = deepcopy(matrix)
    basis.pop("matrix_sha256")
    canonical = json.dumps(
        basis,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_authority_matrix_schema_and_canonical_identity_are_closed() -> None:
    schema = _load(SCHEMA_PATH)
    matrix = _load(MATRIX_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(matrix)
    assert matrix["matrix_sha256"] == _matrix_sha256(matrix)
    assert matrix["matrix_sha256"] == (
        "2cccebe3753385ad1a441b51b776976ec0db9953861ec12a66ab9e27842a1227"
    )


def test_unresolved_or_incompatible_authority_cannot_be_accepted() -> None:
    schema = _load(SCHEMA_PATH)
    matrix = _load(MATRIX_PATH)
    candidate_schema = schema["$defs"]["sourceCandidate"]
    validator = Draft202012Validator(candidate_schema)
    for candidate in matrix["source_candidates"]:
        assert candidate["redistribution_classification"] in PUBLISHABLE
        assert candidate["attribution_required"] is True
        assert candidate["decision"] == "REJECT_CONTRACT_INCOMPATIBLE"
        assert candidate["contract_compatibility"]["status"] == "INCOMPATIBLE"

    invalid = deepcopy(matrix["source_candidates"][0])
    invalid["decision"] = "ACCEPT_FOR_PUBLICATION"
    invalid["redistribution_classification"] = "AUTHORITY_UNRESOLVED"
    assert not validator.is_valid(invalid)


def test_school_requirements_are_recovered_from_the_frozen_profile() -> None:
    matrix = _load(MATRIX_PATH)
    profile = REAL_LAYER_PROFILES["school-point"]
    candidates = [item for item in matrix["source_candidates"] if item["domain"] == "School"]
    assert len(candidates) == 2
    for candidate in candidates:
        requirements = candidate["contract_compatibility"]["verified_requirements"]
        assert requirements == {
            "source_layers": profile["source_layer_ids"],
            "geometry_type": profile["geometry_role"],
            "required_fields": [
                profile["id_field"],
                profile["feature_code_field"],
                profile["label_field"],
            ],
            "terrainid": profile["feature_code"],
            "feature_count": profile["expected_feature_count"],
            "output_crs": "EPSG:4326",
        }
        assert candidate["source_retrieved"] is False
        assert candidate["retrieval_identity"] is None


def test_road_frozen_authorization_rejects_a_new_public_archive_identity() -> None:
    authorization_path = (
        ROOT / "data/specifications/nma-road-hero-road-03-golden-authorization-v1.0.json"
    )
    authorization = _load(authorization_path)
    changed = deepcopy(authorization)
    public_archive_sha256 = "1" * 64
    changed["bindings"]["source_archive_sha256"] = public_archive_sha256
    changed["authorization_sha256"] = authorization_sha256(changed)
    verifier = FrozenRoadAuthorizationVerifier(FrozenRoadInputs(ROOT))
    with pytest.raises(RoadExecutionError) as error:
        verifier.verify(changed, observed_archive_sha256=public_archive_sha256)
    assert error.value.code in {"execution_scope_mismatch", "frozen_identity_mismatch"}

    store = RoadAuthorizationStore(authorization_path)
    with pytest.raises(RoadExecutionError) as missing:
        store.load("public-demo-road-authorization")
    assert missing.value.code == "authorization_not_found"


def test_provenance_chain_is_complete_for_every_rejected_candidate() -> None:
    matrix = _load(MATRIX_PATH)
    for candidate in matrix["source_candidates"]:
        assert candidate["publisher"]
        assert candidate["dataset_title"]
        assert candidate["source_url"].startswith("https://data.gov.tw/")
        assert candidate["license"] == {
            "name": "Open Government Data License",
            "version": "1.0",
            "terms_url": "https://data.gov.tw/license",
        }
        assert len(candidate["evidence"]) >= 2
        assert all(item["url"].startswith("https://data.gov.tw/") for item in candidate["evidence"])
        assert candidate["contract_compatibility"]["blockers"]
        assert candidate["decision"].startswith("REJECT_")


def test_no_fixture_or_demo_authorization_is_published_after_failed_gates() -> None:
    matrix = _load(MATRIX_PATH)
    assert matrix["accepted_public_demo_fixtures"] == []
    assert matrix["demo_authorizations"] == []
    assert matrix["verdict"]["status"] == "fail-closed"
    assert [item["domain"] for item in matrix["domain_decisions"]] == ["School", "ROAD"]
    assert all(item["decision"] == "FAIL_CLOSED" for item in matrix["domain_decisions"])


def test_historical_identity_substitution_is_machine_forbidden() -> None:
    matrix = _load(MATRIX_PATH)
    protection = matrix["historical_identity_protection"]
    assert protection == {
        "demo_fixture_may_claim_historical_equivalence": False,
        "demo_authorization_may_claim_hero03_identity": False,
        "demo_execution_may_claim_frozen_execution_identity": False,
        "demo_hash_may_replace_frozen_hash": False,
    }
    assert matrix["frozen_identities"] == {
        "gen_final": {
            "commit": "380cc6ea2a4498ce83690521c933accfd918818e",
            "tag": "nma-generalization-v1.0-final",
            "immutable": True,
        },
        "build_final": {
            "commit": "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7",
            "tag": "nma-build-v1.0-final",
            "immutable": True,
        },
        "core_final": {
            "commit": "5eb138ae7686502431587743ebce9ddf92c5a799",
            "tag": "nma-core-v1.0-final",
            "immutable": True,
        },
        "road_final": {
            "commit": "325c70d5335f57c43a8af85822db25032aa225c3",
            "tag": "nma-road-v1.0-final",
            "immutable": True,
        },
        "school_hero": {
            "commit": "56f99eb9ae63272a68accac3041fb10eacefb986",
            "tag": None,
            "immutable": True,
        },
    }


def test_frozen_contract_and_domain_files_are_byte_immutable() -> None:
    for relative_path, expected in FROZEN_FILE_SHA256.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected


def test_private_archive_remains_ignored_untracked_and_unstaged() -> None:
    matrix = _load(MATRIX_PATH)
    assert matrix["private_archive_boundary"] == {
        "expected_sha256": "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53",
        "ignored": True,
        "tracked": False,
        "staged": False,
        "extracted": False,
        "inspected": False,
        "used_for_candidate_design": False,
    }
    assert _git("check-ignore", "-q", PRIVATE_ARCHIVE).returncode == 0
    assert _git("ls-files", "--error-unmatch", PRIVATE_ARCHIVE).returncode != 0
    assert PRIVATE_ARCHIVE not in _git("diff", "--cached", "--name-only").stdout.splitlines()


def test_public_reproduction_evidence_has_no_private_payload_dependency() -> None:
    matrix = _load(MATRIX_PATH)
    serialized = json.dumps(matrix, ensure_ascii=False)
    assert 'accepted_public_demo_fixtures": []' in serialized
    assert 'demo_authorizations": []' in serialized
    assert 'source_retrieved": false' in serialized
