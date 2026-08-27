from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator

import build_contracts.building_production_implementation as building
from build_contracts.feature_profile import build_feature_profile
import nma.core as core
from nma.feature_profile_adapters import road_feature_profile, school_feature_profile
from nma.ogr import inspect_dataset
import nma.road_resolution as road
import nma.school_hero_execution as school_execution
import nma.school_hero_verification as school_verification


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT / "data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json"
)
SCHEMA_PATH = ROOT / "schemas/feature-production-generalization-audit-v1.0.schema.json"
REPORT_PATH = ROOT / "GEN-00-Generalization-Audit.md"
BUILD_MANIFEST_PATH = ROOT / "data/specifications/nma-build-final-freeze-manifest-v1.0.json"
BASELINE = "nma-build-v1.0-final"
VERDICT = "PASS — GENERALIZATION PARTIAL; DOMAIN BOUNDARIES REQUIRE CLOSURE"
EXPECTED_GEN00_PATHS = {
    "GEN-00-Generalization-Audit.md",
    "data/specifications/nma-gen-00-feature-production-generalization-audit-v1.0.json",
    "schemas/feature-production-generalization-audit-v1.0.schema.json",
    "tests/test_feature_production_generalization_gen00.py",
}
CLASSIFICATIONS = {
    "canonical-core",
    "generic-candidate",
    "domain-specific",
    "duplicated",
    "intentional-divergence",
    "legacy",
    "indeterminate",
}
DIMENSIONS = [
    "canonical-identity",
    "feature-profile",
    "source-package-binding",
    "schema-validation",
    "evidence-provenance",
    "semantic-mapping",
    "human-policy-authorization",
    "production-contract",
    "geometry-policy",
    "derived-geometry",
    "portrayal-policy",
    "execution-plan",
    "execution-receipt",
    "provenance-chain",
    "observation",
    "verification",
    "fail-closed-behavior",
    "rollback-cleanup",
    "activation-authorization",
    "activation-state",
    "freeze-release-identity",
]


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def _availability(audit: dict[str, object], candidate: str) -> dict[str, object]:
    records = audit["data_availability"]
    assert isinstance(records, list)
    return next(item for item in records if item["candidate"] == candidate)


def test_closed_schema_and_canonical_audit_identity() -> None:
    schema = _load(SCHEMA_PATH)
    audit = _load(AUDIT_PATH)

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(audit)

    basis = deepcopy(audit)
    supplied = basis.pop("audit_sha256")
    assert supplied == core.canonical_sha256(basis)
    assert audit["verdict"] == VERDICT
    assert audit["scope"] == {
        "mode": "audit-and-architecture-definition-only",
        "baseline_ref": BASELINE,
        "baseline_commit": "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7",
        "protected_implementations_modified": False,
        "source_data_modified": False,
        "private_archive_inspected": False,
        "refactoring_authorized": False,
    }


def test_build_final_identity_and_manifest_are_exact() -> None:
    audit = _load(AUDIT_PATH)
    frozen = audit["frozen_identities"]
    assert isinstance(frozen, dict)

    expected = "95de5fa3657a2c8ac7847f1ee1010c48ea984cd7"
    assert _git("rev-parse", "freeze/build-final-95de5fa") == expected
    assert _git("rev-parse", "nma-build-v1.0-final^{}") == expected
    assert _git("cat-file", "-t", "nma-build-v1.0-final") == "tag"
    assert frozen["build_final_sha"] == expected

    manifest = _load(BUILD_MANIFEST_PATH)
    supplied = manifest.pop("canonical_manifest_sha256")
    assert supplied == frozen["build_freeze_manifest_sha256"]
    assert supplied == core.canonical_sha256(manifest)


def test_core_identity_is_canonical_and_feature_profiles_remain_thin() -> None:
    assert road.canonical_json is core.canonical_json
    assert road.canonical_sha256 is core.canonical_sha256
    assert school_execution.canonical_json is core.canonical_json
    assert school_execution.canonical_sha256 is core.canonical_sha256
    assert school_verification.canonical_sha256 is core.canonical_sha256
    assert building.canonical_sha256 is core.canonical_sha256

    profiles = [
        school_feature_profile(),
        road_feature_profile(),
        build_feature_profile(),
    ]
    assert all(isinstance(profile, core.FeatureProfile) for profile in profiles)
    assert [profile.geometry_role for profile in profiles] == [
        "Point",
        "LineString",
        "Polygon",
    ]
    assert profiles[2].metadata["execution_authorized"] is False
    assert not hasattr(core.FeatureProfile, "execute")
    assert not hasattr(core.FeatureProfile, "authorize")


def test_every_component_and_required_dimension_has_one_classification() -> None:
    audit = _load(AUDIT_PATH)
    schema = _load(SCHEMA_PATH)
    assert set(schema["$defs"]["classification"]["enum"]) == CLASSIFICATIONS

    components = audit["existing_primitives"]
    assert isinstance(components, list)
    assert len({item["component"] for item in components}) == len(components)
    assert all(item["classification"] in CLASSIFICATIONS for item in components)

    dimensions = audit["dimensions"]
    assert isinstance(dimensions, list)
    assert [item["id"] for item in dimensions] == DIMENSIONS
    assert all(item["classification"] in CLASSIFICATIONS for item in dimensions)
    assert all(isinstance(item["reusable_contract_justified"], bool) for item in dimensions)

    matrix = audit["duplication_matrix"]
    assert isinstance(matrix, list)
    assert len(matrix) == 21
    assert len({item["capability"] for item in matrix}) == 21
    assert {item["duplication_risk"] for item in matrix} <= {"low", "medium", "high"}


def test_candidate_architecture_preserves_optional_and_domain_owned_boundaries() -> None:
    audit = _load(AUDIT_PATH)
    architecture = audit["candidate_architecture"]
    assert isinstance(architecture, dict)
    assert architecture["supported"] is True
    assert "Optional Activation" in architecture["model"]
    assert "activation authorization" in architecture["conditional_stages"]
    assert "effect rollback" in architecture["conditional_stages"]
    assert "geometry algorithms and invariants" in architecture["domain_owned"]
    assert "portrayal semantics and output-profile values" in architecture["domain_owned"]

    adapters = audit["adapter_boundaries"]
    assert isinstance(adapters, list)
    assert {item["interface"] for item in adapters} == {
        "SourceBinding",
        "SchemaContract",
        "SemanticMapping",
        "GeometryPolicy",
        "PortrayalPolicy",
        "DomainVerifier",
    }
    for adapter in adapters:
        assert set(adapter["owns"]).isdisjoint(adapter["must_not_own"])
    verifier = next(item for item in adapters if item["interface"] == "DomainVerifier")
    assert "execution" in verifier["must_not_own"]
    assert "silent repair or fallback" in verifier["must_not_own"]


def test_duplication_counts_are_repository_evidence_not_text_similarity_only() -> None:
    audit = _load(AUDIT_PATH)
    counts = audit["duplication_quantification"]
    assert isinstance(counts, dict)

    school_schema_count = len(list((ROOT / "schemas").glob("school*.schema.json"))) + 3
    road_schema_count = len(list((ROOT / "schemas").glob("road*.schema.json")))
    build_schema_count = len(list((ROOT / "schemas").glob("build*.schema.json")))
    assert school_schema_count == counts["school_adjacent_schema_files"] == 7
    assert road_schema_count == counts["road_schema_files"] == 15
    assert build_schema_count == counts["build_and_building_schema_files"] == 28
    assert (
        school_schema_count + road_schema_count + build_schema_count
        == counts["domain_schema_family_total"]
        == 50
    )
    assert counts["controlled_execution_surfaces"] == 3
    assert counts["domain_verifier_surfaces"] == 3
    assert "semantic and lifecycle duplication" in counts["interpretation"]


def test_riverl_tracked_source_and_failure_variants_are_real() -> None:
    audit = _load(AUDIT_PATH)
    river = _availability(audit, "RIVERL")
    assert river["status"] == "tracked-source-available"
    assert river["production_source_established"] is True

    tracked = set(_git("ls-files").splitlines())
    component_paths: list[Path] = []
    inspections: dict[str, dict[str, object]] = {}
    for variant in ("clean", "defective", "schema-mismatch", "wrong-crs"):
        root = ROOT / f"data/datasets/authoritative/riverl-{variant}"
        components = [
            root / f"RIVERL{suffix}" for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg")
        ]
        assert all(path.is_file() for path in components)
        assert all(path.relative_to(ROOT).as_posix() in tracked for path in components)
        component_paths.extend(components)
        inspections[variant] = inspect_dataset(root / "RIVERL.shp")

    assert len(component_paths) == 20
    assert all(item["available"] is True for item in inspections.values())
    assert all(item["geometry_type"] == "LineString" for item in inspections.values())
    clean_fields = {item["name"] for item in inspections["clean"]["fields"]}
    mismatch_fields = {item["name"] for item in inspections["schema-mismatch"]["fields"]}
    assert "RIVERLID" in clean_fields
    assert "RIVERID" in mismatch_fields and "RIVERLID" not in mismatch_fields
    assert inspections["clean"]["crs_name"] == "TWD97 / TM2 zone 121"
    assert inspections["wrong-crs"]["crs_name"] == "WGS 84"
    assert "data/specifications/taiwan-5000-riverl-112.json" in tracked


def test_unavailable_candidates_and_private_boundary_are_not_invented() -> None:
    audit = _load(AUDIT_PATH)
    assert _availability(audit, "LANDUSE")["status"] == "not-established"
    assert _availability(audit, "STREAM")["status"] == "unverified-source-availability"
    assert (
        _availability(audit, "POND_OR_FISH_POND")["status"]
        == "portrayal-evidence-only-source-unverified"
    )
    assert _availability(audit, "PRIVATE_SOURCE_ARCHIVE")["status"] == "unknown-not-inspected"

    tracked = _git("ls-files").splitlines()
    source_suffixes = {".shp", ".shx", ".dbf", ".prj", ".cpg", ".vrt", ".csv"}
    tracked_source_names = [
        path for path in tracked if Path(path).suffix.casefold() in source_suffixes
    ]
    assert not [path for path in tracked_source_names if "landuse" in path.casefold()]
    assert not [path for path in tracked_source_names if "stream" in path.casefold()]
    assert not [path for path in tracked_source_names if "pond" in path.casefold()]

    archive = "data/datasets/112年多維度SHP成果_0502.zip"
    assert archive not in tracked
    assert (
        subprocess.run(
            ["git", "check-ignore", "-q", "--", archive], cwd=ROOT, check=False
        ).returncode
        == 0
    )


def test_riverl_is_ranked_first_and_gen01_does_not_start_implementation() -> None:
    audit = _load(AUDIT_PATH)
    ranking = audit["proof_feature_ranking"]
    assert isinstance(ranking, list)
    assert [item["rank"] for item in ranking] == [1, 2, 3, 4]
    assert ranking[0]["candidate"] == "RIVERL"
    assert ranking[0]["recommendation"] == "recommended-later-proof"
    assert ranking[-1]["candidate"] == "LANDUSE"
    assert ranking[-1]["recommendation"] == "do-not-use-as-default-proof"

    gen01 = audit["gen01_recommendation"]
    assert isinstance(gen01, dict)
    assert gen01["title"] == "GEN-01 — Feature Production Contract Boundary Closure"
    assert "frozen implementation migration" in gen01["out_of_scope"]
    assert "RIVERL production implementation" in gen01["out_of_scope"]
    assert "private archive inspection" in gen01["out_of_scope"]
    assert "runtime activation" in gen01["out_of_scope"]


def test_report_returns_one_verdict_and_matches_machine_record() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert report.count(VERDICT) == 1
    assert "A PASS at GEN-00" in report
    assert "does not authorize refactoring" in report
    assert "RIVERL is the strongest candidate" in report
    assert "LANDUSE is not the default proof candidate" in report


def test_gen00_changes_only_four_audit_files_from_frozen_build() -> None:
    changed = set(_git("diff", "--name-only", BASELINE, "--").splitlines())
    untracked = set(_git("ls-files", "--others", "--exclude-standard").splitlines())
    observed = {path for path in changed | untracked if path}

    assert observed == EXPECTED_GEN00_PATHS
    assert not [path for path in observed if path.startswith("src/nma/")]
    assert not [path for path in observed if path.startswith("build_contracts/")]
    assert not [path for path in observed if path.startswith("data/runtime/")]
    assert not [path for path in observed if path.startswith("data/datasets/")]
    assert not [path for path in observed if path.startswith("assets/")]
