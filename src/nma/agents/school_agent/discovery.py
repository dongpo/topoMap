from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal


SchoolSource = Literal["NMA", "OSM", "OFFICIAL_REGISTRY"]


class SchoolAgentError(ValueError):
    """A school-agent input crossed the bounded analysis contract."""


@dataclass(frozen=True)
class SchoolFeature:
    feature_id: str
    name: str
    longitude: float
    latitude: float
    administrative_area: str
    source: SchoolSource
    registry_id: str | None = None
    address: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "name": self.name,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "administrative_area": self.administrative_area,
            "source": self.source,
            "registry_id": self.registry_id,
            "address": self.address,
        }


@dataclass(frozen=True)
class SchoolInventory:
    administrative_area: str
    nma: tuple[SchoolFeature, ...]
    osm: tuple[SchoolFeature, ...]
    official_registry: tuple[SchoolFeature, ...]

    @property
    def feature_count(self) -> int:
        return len(self.nma) + len(self.osm) + len(self.official_registry)


def _read_json(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise SchoolAgentError(f"School dataset does not exist: {source}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SchoolAgentError(f"School dataset is not valid JSON: {source}") from error
    if not isinstance(payload, dict):
        raise SchoolAgentError(f"School dataset must contain a JSON object: {source}")
    return payload


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchoolAgentError(f"School record requires {field}.")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _coordinate(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchoolAgentError(f"School record requires numeric {field}.")
    result = float(value)
    limit = 180 if field == "longitude" else 90
    if not -limit <= result <= limit:
        raise SchoolAgentError(f"School record has invalid {field}.")
    return result


def _geojson_features(payload: dict[str, Any], source: SchoolSource) -> list[SchoolFeature]:
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise SchoolAgentError(f"{source} dataset must be a GeoJSON FeatureCollection.")
    schools: list[SchoolFeature] = []
    for item in payload["features"]:
        if not isinstance(item, dict) or item.get("type") != "Feature":
            raise SchoolAgentError(f"{source} dataset contains an invalid feature.")
        geometry = item.get("geometry")
        properties = item.get("properties")
        if (
            not isinstance(geometry, dict)
            or geometry.get("type") != "Point"
            or not isinstance(geometry.get("coordinates"), list)
            or len(geometry["coordinates"]) < 2
            or not isinstance(properties, dict)
        ):
            raise SchoolAgentError(f"{source} school features require Point geometry and properties.")
        feature_id = item.get("id") or properties.get("feature_id") or properties.get("id")
        if source == "OSM":
            feature_id = feature_id or properties.get("osm_id")
        schools.append(
            SchoolFeature(
                feature_id=_required_text(feature_id, "feature_id"),
                name=_required_text(properties.get("name"), "name"),
                longitude=_coordinate(geometry["coordinates"][0], "longitude"),
                latitude=_coordinate(geometry["coordinates"][1], "latitude"),
                administrative_area=_required_text(
                    properties.get("administrative_area"), "administrative_area"
                ),
                source=source,
                registry_id=_optional_text(properties.get("registry_id")),
                address=_optional_text(properties.get("address")),
            )
        )
    return schools


def load_nma_school_dataset(path: str | Path) -> tuple[SchoolFeature, ...]:
    return tuple(_geojson_features(_read_json(path), "NMA"))


def load_osm_school_pois(path: str | Path) -> tuple[SchoolFeature, ...]:
    return tuple(_geojson_features(_read_json(path), "OSM"))


def load_official_school_registry(path: str | Path) -> tuple[SchoolFeature, ...]:
    payload = _read_json(path)
    records = payload.get("schools")
    if not isinstance(records, list):
        raise SchoolAgentError("Official school registry must contain a schools array.")
    schools: list[SchoolFeature] = []
    for record in records:
        if not isinstance(record, dict):
            raise SchoolAgentError("Official school registry contains an invalid record.")
        registry_id = _required_text(record.get("registry_id"), "registry_id")
        schools.append(
            SchoolFeature(
                feature_id=_required_text(
                    record.get("feature_id") or registry_id, "feature_id"
                ),
                name=_required_text(record.get("name"), "name"),
                longitude=_coordinate(record.get("longitude"), "longitude"),
                latitude=_coordinate(record.get("latitude"), "latitude"),
                administrative_area=_required_text(
                    record.get("administrative_area"), "administrative_area"
                ),
                source="OFFICIAL_REGISTRY",
                registry_id=registry_id,
                address=_optional_text(record.get("address")),
            )
        )
    return tuple(schools)


def _area_filter(
    features: tuple[SchoolFeature, ...], administrative_area: str
) -> tuple[SchoolFeature, ...]:
    expected = administrative_area.casefold()
    return tuple(
        feature
        for feature in features
        if feature.administrative_area.casefold() == expected
    )


def discover_school_features(
    administrative_area: str,
    *,
    nma_dataset: str | Path,
    osm_dataset: str | Path,
    official_registry: str | Path,
) -> SchoolInventory:
    area = _required_text(administrative_area, "administrative_area")
    if len(area) > 160:
        raise SchoolAgentError("Administrative area is limited to 160 characters.")
    inventory = SchoolInventory(
        administrative_area=area,
        nma=_area_filter(load_nma_school_dataset(nma_dataset), area),
        osm=_area_filter(load_osm_school_pois(osm_dataset), area),
        official_registry=_area_filter(load_official_school_registry(official_registry), area),
    )
    return inventory
