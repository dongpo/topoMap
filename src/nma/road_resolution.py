from __future__ import annotations

from copy import deepcopy
from itertools import combinations
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
import unicodedata

from nma.core import canonical_json as canonical_json
from nma.core import canonical_sha256 as canonical_sha256


PACKAGE_SCHEMA = "nma.road-resolution-evidence-package/1.0"
PACKAGE_VERSION = "road-01/1.0"
FIXTURE_SCHEMA = "nma.road-hero-road-01-fixture/1.0"
NORMALIZED_INTENT = (
    "resolve-road|profile=K14|layer=K14_ROAD|class=9420400|"
    "route=縣126|name=中山街|purpose=evidence-package"
)
REQUIRED_EVIDENCE_IDS = (
    "BMAP096-P5-TABLE1-GRAPHIC-ELEMENT-CODES",
    "DOC01-P22-P24-ROAD-BOUNDARY-LABEL",
    "DOC01-P34-P35-ROUTE-SHIELDS",
    "DOC02-P45-P46-ANNEX7-CODING-SCHEME",
    "DOC02-P53-P55-ROAD-CODE-BRANCH",
)
EXPECTED_ADJACENCY = (
    ("K0000004671", "K0000004913"),
    ("K0000004913", "K0000005348"),
)
EXPECTED_ARCHIVE_SHA256 = "4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53"
EXPECTED_FIXTURE_SHA256 = "b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0"
EXPECTED_FEATURE_IDS = ("K0000004671", "K0000004913", "K0000005348")
EXPECTED_IDENTITY = {
    "class_code": "9420400",
    "class_name": "County Highway",
    "route_number": "縣126",
    "road_name": "中山街",
    "canonical_identity": "ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街",
    "identity_basis": ["ROADNUM", "ROADNUM1", "ROADNUM2", "ROADNAME"],
}

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_PATH = ROOT / "data/specifications/nma-road-hero-road-01-v1.0.json"
DEFAULT_EVIDENCE_PATH = ROOT / "data/extraction/v0.4/road-compound-portrayal-reviewed.json"


class RoadResolutionError(ValueError):
    """ROAD-01 rejected a request or a frozen input instead of guessing."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RoadResolutionError(f"{label} is unreadable.", code=f"{label}_unreadable") from error
    if not isinstance(value, dict):
        raise RoadResolutionError(f"{label} must be a JSON object.", code=f"{label}_invalid")
    return value


def _normalized_text(request: str) -> str:
    if not isinstance(request, str) or not request.strip():
        raise RoadResolutionError("The road request is empty.", code="unsupported_request")
    text = unicodedata.normalize("NFKC", request).casefold()
    return " ".join(text.split())


def normalize_road_request(request: str) -> str:
    """Recognize only the bounded K14 County Highway 126 / 中山街 request."""

    text = _normalized_text(request)
    profiles = {
        f"{prefix}{number}"
        for prefix, number in re.findall(r"(?<![a-z0-9])([jk])\s*(\d{2})(?![a-z0-9])", text)
    }
    if profiles != {"k14"}:
        raise RoadResolutionError(
            "The request does not unambiguously identify profile K14.",
            code="unsupported_request",
        )
    if "中山街" not in text:
        raise RoadResolutionError(
            "The request does not identify road name 中山街.", code="unsupported_request"
        )

    route_references = re.findall(r"(?:county\s+highway|縣道|縣)\s*[-#:]?\s*(\d+)", text)
    if set(route_references) != {"126"}:
        raise RoadResolutionError(
            "The request does not unambiguously identify County Highway 126.",
            code="unsupported_request",
        )
    return NORMALIZED_INTENT


def fixture_hash_basis(fixture: Mapping[str, Any]) -> list[Any]:
    identity = fixture.get("road_identity")
    evidence = fixture.get("evidence")
    records = fixture.get("source_records")
    if (
        not isinstance(identity, Mapping)
        or not isinstance(evidence, Mapping)
        or not isinstance(records, list)
    ):
        raise RoadResolutionError(
            "The frozen fixture structure is invalid.", code="fixture_invalid"
        )
    ids = [record.get("feature_id") for record in records if isinstance(record, Mapping)]
    evidence_ids = evidence.get("evidence_ids")
    if len(ids) != len(records) or not isinstance(evidence_ids, list):
        raise RoadResolutionError(
            "The frozen fixture identity is incomplete.", code="fixture_invalid"
        )
    return [
        fixture.get("archive_sha256"),
        fixture.get("profile"),
        fixture.get("layer"),
        identity.get("class_code"),
        identity.get("canonical_identity"),
        ids,
        sorted(evidence_ids),
    ]


def package_hash_basis(package: Mapping[str, Any]) -> dict[str, Any]:
    """Exclude the raw wording and hash field while retaining resolved semantic content."""

    basis = deepcopy(dict(package))
    basis.pop("package_sha256", None)
    request = basis.get("request")
    if isinstance(request, dict):
        request.pop("raw", None)
    return basis


def package_sha256(package: Mapping[str, Any]) -> str:
    return canonical_sha256(package_hash_basis(package))


def _validate_fixture(fixture: Mapping[str, Any], observed_fixture_sha256: str) -> None:
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise RoadResolutionError(
            "The frozen fixture schema is unsupported.", code="fixture_invalid"
        )
    records = fixture.get("source_records")
    evidence = fixture.get("evidence")
    exact_contract = (
        fixture.get("profile") == "K14"
        and fixture.get("layer") == "K14_ROAD"
        and fixture.get("archive_sha256") == EXPECTED_ARCHIVE_SHA256
        and fixture.get("fixture_sha256") == EXPECTED_FIXTURE_SHA256
        and fixture.get("road_identity") == EXPECTED_IDENTITY
        and fixture.get("geometry_type") == "LineString"
        and fixture.get("crs") == "TWD97[2020]_TM121"
        and isinstance(records, list)
        and [record.get("feature_id") for record in records if isinstance(record, Mapping)]
        == list(EXPECTED_FEATURE_IDS)
        and isinstance(evidence, Mapping)
        and evidence.get("record_set") == "nma-road-compound-portrayal-reviewed-v0.4"
        and evidence.get("evidence_ids") == list(REQUIRED_EVIDENCE_IDS)
    )
    if not exact_contract:
        raise RoadResolutionError("The frozen ROAD-00 contract changed.", code="fixture_invalid")
    declared = fixture.get("fixture_sha256")
    computed = canonical_sha256(fixture_hash_basis(fixture))
    if declared != computed or observed_fixture_sha256 != computed:
        raise RoadResolutionError(
            "The frozen fixture SHA-256 does not match.", code="fixture_hash_mismatch"
        )


def _identity_tuple(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("roadnum"),
        record.get("roadnum1"),
        record.get("roadnum2"),
        record.get("roadname"),
    )


def _resolve_records(
    records: Sequence[Mapping[str, Any]], fixture: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    identity = fixture["road_identity"]
    expected_ids = [record["feature_id"] for record in fixture["source_records"]]
    expected_identity = (
        identity["route_number"],
        "",
        "",
        identity["road_name"],
    )
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise RoadResolutionError("Source ROAD records are invalid.", code="source_records_invalid")

    by_id: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(record.get("feature_id"), str):
            raise RoadResolutionError(
                "Source ROAD records are invalid.", code="source_records_invalid"
            )
        feature_id = record["feature_id"]
        if feature_id in by_id:
            raise RoadResolutionError(
                "A source ROAD feature ID is duplicated.", code="duplicate_segment"
            )
        by_id[feature_id] = record

    missing = [feature_id for feature_id in expected_ids if feature_id not in by_id]
    if missing:
        raise RoadResolutionError(
            f"The frozen source segment set is missing {missing!r}.", code="segment_set_mismatch"
        )

    resolved = [by_id[feature_id] for feature_id in expected_ids]
    for record in resolved:
        if record.get("class_code") != identity["class_code"]:
            raise RoadResolutionError(
                "A frozen segment has the wrong road class.", code="class_mismatch"
            )
        if _identity_tuple(record) != expected_identity:
            raise RoadResolutionError(
                "A frozen segment has the wrong logical route identity.",
                code="logical_identity_mismatch",
            )
        if record.get("profile") != fixture["profile"] or record.get("layer") != fixture["layer"]:
            raise RoadResolutionError(
                "A frozen segment has the wrong source binding.", code="source_mismatch"
            )
        if record.get("geometry_type") != fixture["geometry_type"]:
            raise RoadResolutionError(
                "A frozen segment is not a LineString.", code="geometry_mismatch"
            )

    expected_id_set = set(expected_ids)
    extra_matches = [
        record["feature_id"]
        for record in records
        if record["feature_id"] not in expected_id_set
        and record.get("profile") == fixture["profile"]
        and record.get("layer") == fixture["layer"]
        and record.get("class_code") == identity["class_code"]
        and _identity_tuple(record) == expected_identity
    ]
    if extra_matches:
        raise RoadResolutionError(
            f"The logical route has extra source segments {extra_matches!r}.",
            code="segment_set_mismatch",
        )
    return resolved


def _verify_topology(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    endpoints: dict[str, list[str]] = {}
    edges_seen: dict[frozenset[str], str] = {}
    duplicate_count = 0
    self_intersection_count = 0
    overlap_pairs: set[tuple[str, str]] = set()
    ids = [record["feature_id"] for record in records]

    for record in records:
        feature_id = record["feature_id"]
        nodes = record.get("endpoint_nodes")
        if (
            not isinstance(nodes, list)
            or len(nodes) != 2
            or not all(isinstance(node, str) and node for node in nodes)
            or nodes[0] == nodes[1]
        ):
            raise RoadResolutionError(
                "A segment endpoint definition is invalid.", code="topology_mismatch"
            )
        edge = frozenset(nodes)
        if edge in edges_seen:
            duplicate_count += 1
        edges_seen[edge] = feature_id
        for node in nodes:
            endpoints.setdefault(node, []).append(feature_id)
        if record.get("is_simple") is not True:
            self_intersection_count += 1
        overlaps = record.get("positive_length_overlaps")
        if not isinstance(overlaps, list) or not all(item in ids for item in overlaps):
            raise RoadResolutionError("Overlap metadata is invalid.", code="topology_mismatch")
        for other in overlaps:
            if other != feature_id:
                overlap_pairs.add(tuple(sorted((feature_id, other))))

    adjacency_set = {
        tuple(sorted(pair))
        for feature_ids in endpoints.values()
        for pair in combinations(feature_ids, 2)
    }
    expected_adjacency_set = {tuple(sorted(pair)) for pair in EXPECTED_ADJACENCY}
    adjacency = [pair for pair in EXPECTED_ADJACENCY if tuple(sorted(pair)) in adjacency_set]
    adjacency.extend(sorted(adjacency_set - expected_adjacency_set))
    neighbors = {feature_id: set() for feature_id in ids}
    for left, right in adjacency_set:
        neighbors[left].add(right)
        neighbors[right].add(left)
    components = 0
    unseen = set(ids)
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            for neighbor in neighbors[stack.pop()] & unseen:
                unseen.remove(neighbor)
                stack.append(neighbor)

    branch_count = sum(len(feature_ids) > 2 for feature_ids in endpoints.values())
    gap_count = max(components - 1, 0)
    topology = {
        "connected_components": components,
        "adjacency": [list(pair) for pair in adjacency],
        "branch_count": branch_count,
        "gap_count": gap_count,
        "duplicate_segment_count": duplicate_count,
        "positive_length_overlap_count": len(overlap_pairs),
        "self_intersection_count": self_intersection_count,
        "repair_required": False,
    }
    expected = {
        "connected_components": 1,
        "adjacency": [list(pair) for pair in EXPECTED_ADJACENCY],
        "branch_count": 0,
        "gap_count": 0,
        "duplicate_segment_count": 0,
        "positive_length_overlap_count": 0,
        "self_intersection_count": 0,
        "repair_required": False,
    }
    if topology != expected:
        raise RoadResolutionError(
            "The frozen topology does not match ROAD-00.", code="topology_mismatch"
        )
    return topology


def _evidence_ids(record_set: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    for source in record_set.get("sources", []):
        if isinstance(source, Mapping):
            for evidence in source.get("evidence", []):
                if isinstance(evidence, Mapping) and isinstance(evidence.get("record_id"), str):
                    found.add(evidence["record_id"])
    return found


def _bind_evidence(record_set: Mapping[str, Any]) -> dict[str, Any]:
    if record_set.get("record_set_id") != "nma-road-compound-portrayal-reviewed-v0.4":
        raise RoadResolutionError(
            "The reviewed evidence record set changed.", code="evidence_mismatch"
        )
    missing = set(REQUIRED_EVIDENCE_IDS) - _evidence_ids(record_set)
    if missing:
        raise RoadResolutionError(
            f"Required reviewed evidence is missing: {sorted(missing)!r}.",
            code="missing_evidence",
        )

    road_code = next(
        (
            item
            for item in record_set.get("road_codes", [])
            if isinstance(item, Mapping) and item.get("code") == "9420400"
        ),
        None,
    )
    recipe = next(
        (
            item
            for item in record_set.get("compound_road_recipes", [])
            if isinstance(item, Mapping) and item.get("road_code") == "9420400"
        ),
        None,
    )
    graphic_codes = {
        str(item.get("code"))
        for item in record_set.get("graphic_element_type_scheme", {}).get("codes", [])
        if isinstance(item, Mapping)
    }
    if (
        not isinstance(road_code, Mapping)
        or road_code.get("name_zh") != "縣道"
        or str(road_code.get("name_en", "")).casefold() != "county highway"
        or not isinstance(recipe, Mapping)
        or recipe.get("shield_code") != "9490005"
        or recipe.get("shield_orientation") != "road-parallel"
        or not {"2", "5"}.issubset(graphic_codes)
    ):
        raise RoadResolutionError("Reviewed portrayal metadata changed.", code="evidence_mismatch")
    return {
        "record_set": record_set["record_set_id"],
        "evidence_ids": list(REQUIRED_EVIDENCE_IDS),
    }


def resolve_road_request(
    request: str,
    *,
    observed_archive_sha256: str | None = None,
    observed_fixture_sha256: str | None = None,
    source_records: Sequence[Mapping[str, Any]] | None = None,
    fixture: Mapping[str, Any] | None = None,
    evidence_record_set: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve the bounded ROAD-01 request without executing or mutating anything."""

    normalized_intent = normalize_road_request(request)
    frozen = (
        deepcopy(dict(fixture))
        if fixture is not None
        else _load_object(DEFAULT_FIXTURE_PATH, label="fixture")
    )
    fixture_hash = observed_fixture_sha256 or frozen.get("fixture_sha256")
    _validate_fixture(frozen, fixture_hash)

    archive_hash = observed_archive_sha256 or frozen.get("archive_sha256")
    if archive_hash != frozen.get("archive_sha256"):
        raise RoadResolutionError(
            "The source archive SHA-256 does not match ROAD-00.", code="archive_hash_mismatch"
        )

    records = (
        deepcopy(list(source_records))
        if source_records is not None
        else deepcopy(frozen["source_records"])
    )
    resolved = _resolve_records(records, frozen)
    continuity = _verify_topology(resolved)
    reviewed = (
        deepcopy(dict(evidence_record_set))
        if evidence_record_set is not None
        else _load_object(DEFAULT_EVIDENCE_PATH, label="evidence")
    )
    evidence = _bind_evidence(reviewed)
    identity = frozen["road_identity"]

    package: dict[str, Any] = {
        "package_version": PACKAGE_VERSION,
        "schema_version": PACKAGE_SCHEMA,
        "request": {"raw": request, "normalized_intent": normalized_intent},
        "source": {
            "profile": frozen["profile"],
            "layer": frozen["layer"],
            "archive_sha256": archive_hash,
        },
        "road_identity": deepcopy(identity),
        "segment_set": {
            "ordered_feature_ids": [record["feature_id"] for record in resolved],
            "count": len(resolved),
            "geometry_type": frozen["geometry_type"],
            "crs": frozen["crs"],
        },
        "continuity": continuity,
        "evidence": evidence,
        "portrayal": {
            "road_class": identity["class_code"],
            "road_name": identity["road_name"],
            "route_number": identity["route_number"],
            "shield_code": "9490005",
            "shield_orientation": "road-parallel",
            "graphic_element_roles": [2, 5],
        },
        "fixture": {"sha256": fixture_hash},
        "permissions": {
            "source_mutation_allowed": False,
            "execution_allowed": False,
            "topology_repair_allowed": False,
            "roada_execution_allowed": False,
            "road_edge_derivation_allowed": False,
        },
    }
    package["package_sha256"] = package_sha256(package)
    return package
