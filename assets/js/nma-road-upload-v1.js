import {SCHOOL_UPLOAD_LIMITS, SchoolUploadError} from "./nma-school-upload-v1.js";

export const ROAD_UPLOAD_LIMITS = SCHOOL_UPLOAD_LIMITS;

export const ROAD_CODES = Object.freeze({
  "9420100": "國道（需釐清細類）",
  "9420101": "國道高速公路",
  "9420102": "國道快速公路",
  "9420200": "省道（需釐清細類）",
  "9420201": "一般省道",
  "9420202": "省道快速公路",
  "9420300": "市道",
  "9420400": "縣道",
  "9420500": "區道",
  "9420600": "鄉道",
  "9420700": "專用公路",
  "9420800": "市區道路（需釐清細類）",
  "9420801": "一般市區道路",
  "9420802": "市區快速道路",
});

export const ROAD_PARENT_OPTIONS = Object.freeze({
  "9420100": Object.freeze({"9420101": "國道高速公路", "9420102": "國道快速公路"}),
  "9420200": Object.freeze({"9420201": "一般省道", "9420202": "省道快速公路"}),
  "9420800": Object.freeze({"9420801": "一般市區道路", "9420802": "市區快速道路"}),
});

const REQUIRED_COMPONENTS = Object.freeze([".shp", ".shx", ".dbf", ".prj"]);
const OPTIONAL_COMPONENTS = Object.freeze([".cpg"]);

export class RoadUploadError extends SchoolUploadError {
  constructor(code, message) {
    super(code, message);
    this.name = "RoadUploadError";
  }
}

function assert(condition, code, message) {
  if (!condition) throw new RoadUploadError(code, message);
}

function componentExtension(name) {
  const match = name.toLowerCase().match(/\.(shp|shx|dbf|prj|cpg)$/);
  return match ? `.${match[1]}` : null;
}

export function validateRoadArchive(file, entries) {
  assert(file?.name?.toLowerCase().endsWith(".zip"), "zip-required", "請上傳 `.zip` 檔案。");
  assert(file.size > 0, "empty-archive", "ZIP 檔案是空的。");
  assert(
    file.size <= ROAD_UPLOAD_LIMITS.archiveBytes,
    "archive-too-large",
    "ZIP 超過 16 MiB；ROAD browser preview 不接受更大的上傳。",
  );
  assert(Array.isArray(entries) && entries.length > 0, "empty-archive", "ZIP 沒有檔案項目。");
  const componentEntries = entries.filter((entry) => componentExtension(entry.name));
  assert(componentEntries.length > 0, "shapefile-missing", "ZIP 中找不到 Shapefile 元件。");
  const groups = new Map();
  for (const entry of componentEntries) {
    const extension = componentExtension(entry.name);
    const base = entry.lowerName.slice(0, -extension.length);
    if (!groups.has(base)) groups.set(base, new Map());
    const components = groups.get(base);
    assert(!components.has(extension), "duplicate-component", `ZIP 重複包含 ${base}${extension}。`);
    components.set(extension, entry);
  }
  assert(groups.size === 1, "multiple-shapefiles", "ROAD demo 每次只接受一個 Shapefile 圖層。");
  const [[base, components]] = groups.entries();
  const missing = REQUIRED_COMPONENTS.filter((extension) => !components.has(extension));
  assert(missing.length === 0, "required-component-missing", `缺少必要元件：${missing.join("、")}。`);
  const layerName = base.split("/").at(-1);
  assert(
    layerName === "road" || layerName.endsWith("_road"),
    "road-layer-required",
    "ROAD demo 只接受 ROAD 線圖層（檔名需為 ROAD 或 *_ROAD）。",
  );
  return {
    layerName,
    zipRelativeBase: base,
    requiredComponents: REQUIRED_COMPONENTS.map((extension) => components.get(extension).name),
    optionalComponents: OPTIONAL_COMPONENTS.filter((extension) => components.has(extension)).map(
      (extension) => components.get(extension).name,
    ),
    componentCount: components.size,
  };
}

function normalizedFeatureCollection(parsed) {
  if (Array.isArray(parsed)) {
    assert(parsed.length === 1, "multiple-shapefiles", "解析結果包含多個 Shapefile 圖層。");
    return parsed[0];
  }
  if (parsed?.type === "FeatureCollection") return parsed;
  if (parsed && typeof parsed === "object") {
    const collections = Object.values(parsed).filter((item) => item?.type === "FeatureCollection");
    assert(collections.length === 1, "multiple-shapefiles", "解析結果不是單一 Shapefile 圖層。");
    return collections[0];
  }
  throw new RoadUploadError("invalid-shapefile", "Shapefile 無法解析為 FeatureCollection。");
}

function coordinateArrays(geometry) {
  if (geometry.type === "LineString") return [geometry.coordinates];
  if (geometry.type === "MultiLineString") return geometry.coordinates;
  throw new RoadUploadError("wrong-geometry", "ROAD 圖層只能包含 LineString 或 MultiLineString geometry。");
}

function inspectCoordinates(geometry, featureNumber) {
  let count = 0;
  for (const line of coordinateArrays(geometry)) {
    assert(Array.isArray(line) && line.length >= 2, "invalid-line", `第 ${featureNumber} 筆道路線少於兩個 vertex。`);
    for (const coordinate of line) {
      assert(
        Array.isArray(coordinate) &&
          coordinate.length >= 2 &&
          Number.isFinite(coordinate[0]) &&
          Number.isFinite(coordinate[1]) &&
          coordinate[0] >= -180 &&
          coordinate[0] <= 180 &&
          coordinate[1] >= -90 &&
          coordinate[1] <= 90,
        "crs-transform-failed",
        "座標未成功轉換為 WGS84；請檢查 `.prj` 是否正確。",
      );
      count += 1;
    }
  }
  return count;
}

function detectClassificationField(properties) {
  if (Object.hasOwn(properties, "ROADCLASS2")) return "ROADCLASS2";
  if (Object.hasOwn(properties, "TERRAINID")) return "TERRAINID";
  throw new RoadUploadError(
    "classification-field-missing",
    "找不到 Document 09 的 ROADCLASS2，也找不到可問答確認的 TERRAINID；資料檢查已終止。",
  );
}

function validActor(value) {
  return /^[A-Za-z0-9._:@-]{1,120}$/.test(value || "");
}

export function inspectRoadFeatures(parsed, archive, options = {}) {
  const input = normalizedFeatureCollection(parsed);
  const features = input.features;
  assert(Array.isArray(features) && features.length > 0, "no-features", "Shapefile 沒有圖徵。");
  assert(
    features.length <= ROAD_UPLOAD_LIMITS.featureCount,
    "too-many-features",
    `單一 ROAD 圖層最多接受 ${ROAD_UPLOAD_LIMITS.featureCount.toLocaleString()} 筆線圖徵。`,
  );
  const firstProperties = features[0]?.properties;
  assert(firstProperties && typeof firstProperties === "object", "properties-missing", "第一筆圖徵缺少屬性。");
  const classificationField = detectClassificationField(firstProperties);
  const rawCounts = {};
  const identities = new Set();
  let totalVertexCount = 0;
  let multipartFeatureCount = 0;
  let namedFeatureCount = 0;
  let numberedFeatureCount = 0;
  const vertexCounts = [];
  const collection = structuredClone(input);
  for (const [index, feature] of collection.features.entries()) {
    const number = index + 1;
    const properties = feature?.properties;
    assert(properties && typeof properties === "object", "properties-missing", `第 ${number} 筆缺少屬性。`);
    for (const field of ["ROADSEGID", classificationField, "ROADNAME", "ROADNUM", "ROADNUM1", "ROADNUM2"]) {
      assert(Object.hasOwn(properties, field), "required-field-missing", `缺少必要欄位 ${field}；資料檢查已終止。`);
    }
    assert(
      feature.geometry?.type === "LineString" || feature.geometry?.type === "MultiLineString",
      "wrong-geometry",
      "ROAD 圖層只能包含 LineString 或 MultiLineString geometry。",
    );
    const vertexCount = inspectCoordinates(feature.geometry, number);
    totalVertexCount += vertexCount;
    vertexCounts.push(vertexCount);
    if (feature.geometry.type === "MultiLineString") multipartFeatureCount += 1;
    const sourceId = String(properties.ROADSEGID ?? "").trim();
    assert(sourceId, "empty-roadsegid", `第 ${number} 筆 ROADSEGID 是空白。`);
    const identity = `${archive.zipRelativeBase}::${sourceId}`;
    assert(!identities.has(identity), "duplicate-identity", `filename + ROADSEGID 不唯一：${identity}。`);
    identities.add(identity);
    const code = String(properties[classificationField] ?? "").trim();
    assert(
      Object.hasOwn(ROAD_CODES, code),
      "invalid-road-classification",
      `第 ${number} 筆 ${classificationField}=${code || "(空白)"} 不在目前已審查的道路分類範圍。`,
    );
    rawCounts[code] = (rawCounts[code] || 0) + 1;
    if (String(properties.ROADNAME ?? "").trim()) namedFeatureCount += 1;
    if (["ROADNUM", "ROADNUM1", "ROADNUM2"].some((field) => String(properties[field] ?? "").trim())) {
      numberedFeatureCount += 1;
    }
  }

  const clarifications = [];
  if (classificationField === "TERRAINID" && !validActor(options.schemaMappingConfirmedBy)) {
    clarifications.push({
      type: "schema-field-mapping",
      sourceField: "TERRAINID",
      canonicalField: "ROADCLASS2",
      question: "這份 ROAD Shapefile 的 TERRAINID 是否承載附件七道路分類編碼？",
    });
  }
  for (const sourceCode of Object.keys(rawCounts).filter((code) => ROAD_PARENT_OPTIONS[code])) {
    const effectiveCode = options.parentResolutions?.[sourceCode];
    if (!Object.hasOwn(ROAD_PARENT_OPTIONS[sourceCode], effectiveCode || "")) {
      clarifications.push({
        type: "parent-classification",
        sourceCode,
        sourceName: ROAD_CODES[sourceCode],
        count: rawCounts[sourceCode],
        options: ROAD_PARENT_OPTIONS[sourceCode],
        question: `${sourceCode} 是父分類；這 ${rawCounts[sourceCode]} 筆資料實際屬於哪一個已審查子類？`,
      });
    }
  }
  if (clarifications.length) {
    return {
      status: "clarification-required",
      collection,
      classificationField,
      rawCounts,
      clarifications,
      preliminary: {featureCount: features.length, totalVertexCount, multipartFeatureCount},
    };
  }

  const confirmedBy = classificationField === "TERRAINID" ? options.schemaMappingConfirmedBy : null;
  if (classificationField === "TERRAINID") {
    assert(validActor(confirmedBy), "mapping-reviewer-invalid", "請提供本次 schema mapping 的審查者識別。");
  }
  const resolutions = [];
  const counts = {};
  for (const feature of collection.features) {
    const sourceCode = String(feature.properties[classificationField]).trim();
    const effectiveCode = options.parentResolutions?.[sourceCode] || sourceCode;
    feature.properties.__NMA_ROAD_CLASS = effectiveCode;
    counts[effectiveCode] = (counts[effectiveCode] || 0) + 1;
  }
  for (const sourceCode of Object.keys(rawCounts).filter((code) => ROAD_PARENT_OPTIONS[code])) {
    resolutions.push({
      source_code: sourceCode,
      effective_code: options.parentResolutions[sourceCode],
      status: "session-human-confirmed",
      confirmed_by: options.parentResolutionConfirmedBy,
    });
  }
  if (resolutions.length) {
    assert(
      validActor(options.parentResolutionConfirmedBy),
      "classification-reviewer-invalid",
      "請提供本次父分類釐清的審查者識別。",
    );
  }
  return {
    status: "ready",
    collection,
    observation: {
      sourceLayer: "ROAD",
      geometryFamily: "line",
      geometryTypes: [...new Set(collection.features.map((feature) => feature.geometry.type))].sort(),
      classificationField,
      classificationFieldMapping: {
        source_field: classificationField,
        canonical_field: "ROADCLASS2",
        status: classificationField === "ROADCLASS2" ? "official-direct" : "session-human-confirmed",
        confirmed_by: confirmedBy,
      },
      identityField: "ROADSEGID",
      labelField: "ROADNAME",
      routeNumberFields: ["ROADNUM", "ROADNUM1", "ROADNUM2"],
      observedClassCounts: counts,
      classificationResolutions: resolutions,
      featureCount: features.length,
      totalVertexCount,
      vertexCounts,
      multipartFeatureCount,
      namedFeatureCount,
      numberedFeatureCount,
      sourceIdentityRule: "zip-relative-filename-plus-source-id",
      outputCrs: "EPSG:4326",
      rawFeatureBytesTransmitted: false,
    },
  };
}
