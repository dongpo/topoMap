from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping


RQ1_REQUIREMENTS = (
    ("classification", "classification"),
    ("geometry", "geometry"),
    ("line_style", "line style"),
    ("color", "color"),
    ("source_evidence", "source evidence"),
    ("unresolved_binding", "unresolved ProductLayer binding"),
)

_UNRESOLVED_WORDS = (
    "unresolved",
    "unconfirmed",
    "not confirmed",
    "no confirmed",
    "unknown",
    "未解析",
    "未確認",
    "未确认",
    "尚未確認",
    "尚未确认",
    "無確認",
    "无确认",
)
_BINDING_WORDS = (
    "binding",
    "productlayer",
    "product layer",
    "product-layer",
    "schema",
    "field",
    "產品圖層",
    "产品图层",
    "欄位",
    "字段",
)
_COLOR_ALIASES = {
    "black": "black",
    "黑色": "black",
    "red": "red",
    "紅色": "red",
    "红色": "red",
    "blue": "blue",
    "藍色": "blue",
    "蓝色": "blue",
    "green": "green",
    "綠色": "green",
    "绿色": "green",
    "white": "white",
    "白色": "white",
    "yellow": "yellow",
    "黃色": "yellow",
    "黄色": "yellow",
    "gray": "gray",
    "grey": "gray",
    "灰色": "gray",
}
_GEOMETRY_ALIASES = {
    "point": "Point",
    "點": "Point",
    "点": "Point",
    "點狀幾何": "Point",
    "点状几何": "Point",
    "linestring": "LineString",
    "line string": "LineString",
    "polygon": "Polygon",
    "curve": "Curve",
}


def _empty_evidence() -> dict[str, Any]:
    return {
        "feature_code": {},
        "feature_name": {},
        "geometry": {},
        "line_style": {},
        "color_code": {},
        "color_name": {},
        "source_page": {},
        "printed_page": {},
        "document_id": {},
        "document_name": {},
        "record_id": {},
        "revision": {},
        "activation_status": {},
        "product_layer": {},
        "mapping_unresolved": False,
        "mapping_evidence_ids": [],
        "printed_page_unknown": False,
    }


def _add_value(normalized: dict[str, Any], category: str, value: object, evidence_id: str) -> None:
    if value is None or isinstance(value, (dict, list)):
        return
    rendered = str(value).strip()
    if not rendered:
        return
    normalized[category].setdefault(rendered, [])
    if evidence_id not in normalized[category][rendered]:
        normalized[category][rendered].append(evidence_id)


def _signals_unresolved(value: object) -> bool:
    rendered = str(value).casefold()
    return any(word in rendered for word in _UNRESOLVED_WORDS)


def normalize_validation_evidence(
    evidence_package: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a bounded validation-only view of already retrieved evidence."""

    normalized = _empty_evidence()
    for node in evidence_package.get("evidence_nodes", []):
        if not isinstance(node, Mapping) or not isinstance(node.get("id"), str):
            continue
        node_id = node["id"]
        node_type = node.get("type")
        properties = node.get("properties", {})
        if not isinstance(properties, Mapping):
            continue
        if node_type in {"ClassificationCode", "PortrayalRule"}:
            _add_value(
                normalized,
                "feature_code",
                properties.get("code", properties.get("feature_code")),
                node_id,
            )
            _add_value(
                normalized,
                "feature_name",
                properties.get("label", properties.get("feature_name")),
                node_id,
            )
        if node_type == "PortrayalGeometryRole" or "geometry_role" in properties:
            _add_value(
                normalized,
                "geometry",
                properties.get("name", properties.get("geometry_role")),
                node_id,
            )
        if node_type == "LineStyleReference":
            _add_value(normalized, "line_style", properties.get("code"), node_id)
        if node_type == "PortrayalColorReference":
            _add_value(normalized, "color_code", properties.get("code"), node_id)
            _add_value(normalized, "color_name", properties.get("observed_color"), node_id)
        if node_type == "SpecificationDocument":
            _add_value(normalized, "document_id", node_id, node_id)
            _add_value(normalized, "document_name", properties.get("filename"), node_id)
            _add_value(normalized, "revision", properties.get("revision"), node_id)
        if node_type == "DocumentSection":
            _add_value(normalized, "record_id", properties.get("record_id"), node_id)
        _add_value(normalized, "activation_status", properties.get("activation_status"), node_id)
        _add_value(normalized, "product_layer", properties.get("product_layer"), node_id)
        mapping_status = properties.get("mapping_status")
        if mapping_status is not None and _signals_unresolved(mapping_status):
            normalized["mapping_unresolved"] = True
            normalized["mapping_evidence_ids"].append(node_id)

    for citation in evidence_package.get("citations", []):
        if not isinstance(citation, Mapping):
            continue
        citation_id = str(citation.get("citation_id", "citation:unknown"))
        _add_value(normalized, "source_page", citation.get("page"), citation_id)
        if citation.get("printed_page") is None:
            normalized["printed_page_unknown"] = True
        else:
            _add_value(normalized, "printed_page", citation.get("printed_page"), citation_id)
        _add_value(normalized, "document_id", citation.get("document_id"), citation_id)
        _add_value(normalized, "document_name", citation.get("filename"), citation_id)
        _add_value(normalized, "record_id", citation.get("record_id"), citation_id)
        _add_value(normalized, "revision", citation.get("revision"), citation_id)
    return normalized


def _claim(
    *,
    text: str,
    category: str,
    value: object,
    start: int,
    end: int,
) -> dict[str, Any]:
    return {
        "text": text[start:end],
        "normalized_claim": {"category": category, "value": value},
        "_start": start,
        "_end": end,
    }


def _regex_claims(
    answer: str,
    pattern: str,
    *,
    category: str,
    flags: int = re.IGNORECASE,
    normalizer=lambda value: value,
) -> list[dict[str, Any]]:
    claims = []
    for match in re.finditer(pattern, answer, flags):
        claims.append(
            _claim(
                text=answer,
                category=category,
                value=normalizer(match.group(1)),
                start=match.start(),
                end=match.end(),
            )
        )
    return claims


def extract_atomic_claims(
    answer: str, normalized_evidence: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Extract only bounded RQ1 propositions; do not rewrite or complete the answer."""

    claims: list[dict[str, Any]] = []
    claims.extend(
        _regex_claims(
            answer,
            r"(?<!\d)(\d{7})(?!\d)",
            category="feature_code",
        )
    )
    for value in normalized_evidence.get("feature_name", {}):
        for match in re.finditer(re.escape(value), answer, re.IGNORECASE):
            claims.append(
                _claim(
                    text=answer,
                    category="feature_name",
                    value=value,
                    start=match.start(),
                    end=match.end(),
                )
            )

    geometry_pattern = (
        r"(point(?:\s+(?:geometry|feature))?|linestring|line string|polygon|curve|"
        r"點狀幾何|点状几何|(?:(?:geometry|幾何|几何)\s*(?:is|為|为|=|:|：)?\s*)[點点])"
    )

    def normalize_geometry(value: str) -> str:
        cleaned = value.casefold().strip()
        if cleaned.endswith(" geometry") or cleaned.endswith(" feature"):
            cleaned = cleaned.rsplit(" ", 1)[0]
        if cleaned.startswith(("geometry", "幾何", "几何")):
            cleaned = cleaned[-1]
        return _GEOMETRY_ALIASES.get(cleaned, value)

    claims.extend(
        _regex_claims(
            answer,
            geometry_pattern,
            category="geometry",
            normalizer=normalize_geometry,
        )
    )
    claims.extend(
        _regex_claims(
            answer,
            r"(?:line[\s-]?style|line\s+type|線型|线型|線式|线式|線號|线号)"
            r"\s*(?:code|identifier|id|代碼|代码|碼|号|號)?\s*"
            r"(?:is|為|为|=|:|：)?\s*(?:code\s*)?([0-9]+)",
            category="line_style",
        )
    )
    claims.extend(
        _regex_claims(
            answer,
            r"(?:color|colour|顏色|颜色|色碼|色码)\s*"
            r"(?:code|identifier|id|代碼|代码|碼)?\s*(?:is|為|为|=|:|：)?\s*([0-9]+)",
            category="color_code",
        )
    )
    for alias, canonical in _COLOR_ALIASES.items():
        boundary = r"\b" if alias.isascii() else ""
        for match in re.finditer(boundary + re.escape(alias) + boundary, answer, re.IGNORECASE):
            claims.append(
                _claim(
                    text=answer,
                    category="color_name",
                    value=canonical,
                    start=match.start(),
                    end=match.end(),
                )
            )

    printed_spans: list[tuple[int, int]] = []
    printed_pattern = (
        r"(?:printed[ _-]?page|打印[頁页]|印刷[頁页])\s*(?:is|為|为|=|:|：)?\s*"
        r"([0-9]+|unknown|not stated|未記載|未记载|未知)"
    )
    for match in re.finditer(printed_pattern, answer, re.IGNORECASE):
        value = match.group(1)
        normalized_value: object = None if not value.isdigit() else value
        claims.append(
            _claim(
                text=answer,
                category="printed_page",
                value=normalized_value,
                start=match.start(),
                end=match.end(),
            )
        )
        printed_spans.append((match.start(), match.end()))

    page_patterns = (
        r"(?:pdf\s*)?page\s*(?:is|=|:|：|-)?\s*([0-9]+)",
        r"第?\s*([0-9]+)\s*[頁页]",
    )
    for pattern in page_patterns:
        for item in _regex_claims(answer, pattern, category="source_page"):
            if not any(
                item["_start"] < end and item["_end"] > start for start, end in printed_spans
            ):
                claims.append(item)

    claims.extend(
        _regex_claims(
            answer,
            r"(?:revision|版本|修訂|修订)\s*(?:is|為|为|=|:|：)?\s*"
            r"([A-Za-z0-9_]+(?:[.-][A-Za-z0-9_]+)*)",
            category="revision",
        )
    )
    for category in ("document_id", "document_name", "record_id"):
        for value in normalized_evidence.get(category, {}):
            for match in re.finditer(re.escape(value), answer, re.IGNORECASE):
                claims.append(
                    _claim(
                        text=answer,
                        category=category,
                        value=value,
                        start=match.start(),
                        end=match.end(),
                    )
                )

    sentence_pattern = re.compile(r"[^.;。；\n]+")
    for sentence in sentence_pattern.finditer(answer):
        sentence_lower = sentence.group(0).casefold()
        if any(word in sentence_lower for word in _BINDING_WORDS) and any(
            word in sentence_lower for word in _UNRESOLVED_WORDS
        ):
            claims.append(
                _claim(
                    text=answer,
                    category="mapping_unresolved",
                    value=True,
                    start=sentence.start(),
                    end=sentence.end(),
                )
            )
    concrete_binding = re.compile(
        r"(?:product\s*layer|productlayer|產品圖層|产品图层|binding)\s*"
        r"(?:is|為|为|=|:|：|to)\s*([\w-]+(?:[.-][\w-]+)*)",
        re.IGNORECASE,
    )
    for match in concrete_binding.finditer(answer):
        value = match.group(1)
        if not any(word in value.casefold() for word in _UNRESOLVED_WORDS):
            claims.append(
                _claim(
                    text=answer,
                    category="product_layer",
                    value=value,
                    start=match.start(),
                    end=match.end(),
                )
            )

    for value in normalized_evidence.get("activation_status", {}):
        for match in re.finditer(re.escape(value), answer, re.IGNORECASE):
            claims.append(
                _claim(
                    text=answer,
                    category="activation_status",
                    value=value,
                    start=match.start(),
                    end=match.end(),
                )
            )

    deduplicated: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for item in claims:
        key = (
            item["normalized_claim"]["category"],
            str(item["normalized_claim"]["value"]),
            item["_start"],
            item["_end"],
        )
        deduplicated[key] = item
    return sorted(
        deduplicated.values(),
        key=lambda item: (item["_start"], item["_end"], item["normalized_claim"]["category"]),
    )


def _casefold_values(values: Mapping[str, Any]) -> dict[str, str]:
    return {str(value).casefold(): str(value) for value in values}


def ground_claims(
    claims: list[dict[str, Any]], normalized_evidence: Mapping[str, Any]
) -> dict[str, Any]:
    evaluated = []
    for raw_claim in claims:
        item = deepcopy(raw_claim)
        item.pop("_start", None)
        item.pop("_end", None)
        category = item["normalized_claim"]["category"]
        value = item["normalized_claim"]["value"]
        evidence_ids: list[str] = []
        evidence_values: list[str] = []
        if category == "mapping_unresolved":
            supported = normalized_evidence.get("mapping_unresolved") is True
            status = "SUPPORTED" if supported else "UNSUPPORTED"
            evidence_ids = list(normalized_evidence.get("mapping_evidence_ids", []))
            reason = (
                "retrieved mapping_status explicitly preserves an unresolved binding"
                if supported
                else "retrieved evidence does not establish an unresolved binding"
            )
        elif category == "printed_page" and value is None:
            supported = normalized_evidence.get("printed_page_unknown") is True
            status = "SUPPORTED" if supported else "CONTRADICTED"
            reason = (
                "retrieved citation metadata records printed_page as unknown"
                if supported
                else "retrieved citation metadata contains a concrete printed page"
            )
        elif category == "product_layer" and normalized_evidence.get("mapping_unresolved"):
            status = "CONTRADICTED"
            evidence_ids = list(normalized_evidence.get("mapping_evidence_ids", []))
            reason = "a concrete ProductLayer binding conflicts with explicit unresolved status"
        else:
            values = normalized_evidence.get(category, {})
            if not isinstance(values, Mapping):
                values = {}
            by_casefold = _casefold_values(values)
            matched = by_casefold.get(str(value).casefold())
            if matched is not None:
                status = "SUPPORTED"
                evidence_values = [matched]
                evidence_ids = list(values[matched])
                reason = "normalized claim value matches retrieved authoritative evidence"
            elif values:
                status = "CONTRADICTED"
                evidence_values = list(values)
                reason = "claim value conflicts with retrieved authoritative values"
            else:
                status = "UNSUPPORTED"
                reason = "no supporting value exists in the retrieved validation evidence"
        item.update(
            {
                "status": status,
                "evidence_ids": evidence_ids,
                "evidence_values": evidence_values,
                "reason": reason,
            }
        )
        evaluated.append(item)

    counts = {
        status.casefold() + "_count": sum(item["status"] == status for item in evaluated)
        for status in ("SUPPORTED", "UNSUPPORTED", "CONTRADICTED", "UNVERIFIABLE")
    }
    return {
        "verdict": (
            "PASS"
            if counts["unsupported_count"] == 0 and counts["contradicted_count"] == 0
            else "FAIL"
        ),
        "total_factual_claims": len(evaluated),
        "claims": evaluated,
        **counts,
    }


def _category_mentions(answer: str, markers: tuple[str, ...]) -> bool:
    lowered = answer.casefold()
    return any(marker in lowered for marker in markers)


def evaluate_rq1_coverage(answer: str, claims: list[dict[str, Any]]) -> dict[str, Any]:
    categories: dict[str, list[dict[str, Any]]] = {}
    for item in claims:
        categories.setdefault(item["normalized_claim"]["category"], []).append(item)

    rules = {
        "classification": (
            {"feature_code", "feature_name"},
            ("classification", "class", "feature code", "分類", "分类", "代碼", "代码"),
        ),
        "geometry": ({"geometry"}, ("geometry", "幾何", "几何")),
        "line_style": (
            {"line_style"},
            ("line style", "line-style", "line type", "線型", "线型", "線式", "线式"),
        ),
        "color": (
            {"color_code", "color_name"},
            ("color", "colour", "顏色", "颜色", "色碼", "色码"),
        ),
        "source_evidence": (
            {
                "source_page",
                "printed_page",
                "document_id",
                "document_name",
                "record_id",
                "revision",
            },
            (
                "source",
                "evidence",
                "citation",
                "document",
                "page",
                "來源",
                "来源",
                "證據",
                "证据",
                "頁",
                "页",
            ),
        ),
        "unresolved_binding": (
            {"mapping_unresolved", "product_layer"},
            _BINDING_WORDS,
        ),
    }
    requirements = []
    for requirement_id, label in RQ1_REQUIREMENTS:
        claim_categories, mention_markers = rules[requirement_id]
        matched = [item for category in claim_categories for item in categories.get(category, [])]
        status = (
            "PASS"
            if matched
            else "PARTIAL"
            if _category_mentions(answer, mention_markers)
            else "FAIL"
        )
        requirements.append(
            {
                "id": requirement_id,
                "label": label,
                "status": status,
                "matched_text": [item["text"] for item in matched],
            }
        )
    return {
        "verdict": ("PASS" if all(item["status"] == "PASS" for item in requirements) else "FAIL"),
        "requirements": requirements,
    }


def validate_rq1_answer(
    output: Mapping[str, Any], evidence_package: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate the displayed RQ1 answer post hoc without changing it or calling a model."""

    answer = output.get("answer")
    if not isinstance(answer, str):
        raise ValueError("RQ1 validation requires the displayed answer text.")
    node_ids = list(output.get("evidence_node_ids", []))
    citation_ids = list(output.get("citation_ids", []))
    valid_nodes = {
        item["id"]
        for item in evidence_package.get("evidence_nodes", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    valid_citations = {
        item["citation_id"]
        for item in evidence_package.get("citations", [])
        if isinstance(item, Mapping) and isinstance(item.get("citation_id"), str)
    }
    evidence_ids_valid = len(node_ids) == len(set(node_ids)) and set(node_ids) <= valid_nodes
    citation_ids_valid = (
        len(citation_ids) == len(set(citation_ids)) and set(citation_ids) <= valid_citations
    )
    normalized_evidence = normalize_validation_evidence(evidence_package)
    extracted = extract_atomic_claims(answer, normalized_evidence)
    grounding = ground_claims(extracted, normalized_evidence)
    coverage = evaluate_rq1_coverage(answer, extracted)
    reference_integrity = {
        "verdict": "PASS" if evidence_ids_valid and citation_ids_valid else "FAIL",
        "evidence_ids_valid": evidence_ids_valid,
        "citation_ids_valid": citation_ids_valid,
    }
    overall = (
        "PASS"
        if reference_integrity["verdict"] == grounding["verdict"] == coverage["verdict"] == "PASS"
        else "FAIL"
    )
    return {
        "schema": "nma.rq1-answer-validation/1.0",
        "reference_integrity": reference_integrity,
        "claim_grounding": grounding,
        "question_coverage": coverage,
        "overall_verdict": overall,
        "validated_answer": answer,
        "answer_unchanged": answer == output.get("answer"),
        "validation_model_calls": 0,
        "grounding_policy": (
            "FAIL on any UNSUPPORTED or CONTRADICTED claim; surface UNVERIFIABLE separately"
        ),
        "normalized_evidence": normalized_evidence,
    }
