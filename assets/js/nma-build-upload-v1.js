import {SCHOOL_UPLOAD_LIMITS, SchoolUploadError} from "./nma-school-upload-v1.js";

export const BUILD_UPLOAD_LIMITS = Object.freeze({...SCHOOL_UPLOAD_LIMITS, vertexCount: 1_000_000});

export const BUILD_CODES = Object.freeze({
  "9310000": "建物（需釐清細類）",
  "9310100": "永久性建物（建築區）",
  "9310103": "無牆建物",
  "9310200": "建築中建物",
  "9310300": "臨時性建物",
});

export const BUILD_PARENT_OPTIONS = Object.freeze({
  "9310000": Object.freeze({
    "9310100": "永久性建物（建築區）",
    "9310200": "建築中建物",
    "9310300": "臨時性建物",
  }),
});

export const BUILD_SCHEMA_FIELDS = Object.freeze([
  "BUILD_ID",
  "TERRAINID",
  "BUILD_STR",
  "BUILD_NO",
  "BUILD_H",
  "GROUP_ID",
  "MDATE",
]);

const REQUIRED_COMPONENTS = Object.freeze([".shp", ".shx", ".dbf", ".prj"]);
const OPTIONAL_COMPONENTS = Object.freeze([".cpg"]);

export class BuildUploadError extends SchoolUploadError {
  constructor(code, message) {
    super(code, message);
    this.name = "BuildUploadError";
  }
}

function assert(condition, code, message) {
  if (!condition) throw new BuildUploadError(code, message);
}

function componentExtension(name) {
  const match = name.toLowerCase().match(/\.(shp|shx|dbf|prj|cpg)$/);
  return match ? `.${match[1]}` : null;
}

export function validateBuildArchive(file, entries) {
  assert(file?.name?.toLowerCase().endsWith(".zip"), "zip-required", "請上傳 `.zip` 檔案。");
  assert(file.size > 0, "empty-archive", "ZIP 檔案是空的。");
  assert(
    file.size <= BUILD_UPLOAD_LIMITS.archiveBytes,
    "archive-too-large",
    "ZIP 超過 16 MiB；BUILD browser preview 不接受更大的上傳。",
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
  assert(groups.size === 1, "multiple-shapefiles", "BUILD demo 每次只接受一個 Shapefile 圖層。");
  const [[base, components]] = groups.entries();
  const missing = REQUIRED_COMPONENTS.filter((extension) => !components.has(extension));
  assert(missing.length === 0, "required-component-missing", `缺少必要元件：${missing.join("、")}。`);
  const layerName = base.split("/").at(-1);
  assert(
    layerName === "build" || layerName.endsWith("_build"),
    "build-layer-required",
    "BUILD demo 只接受 BUILD 面圖層（檔名需為 BUILD 或 *_BUILD）。",
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
  throw new BuildUploadError("invalid-shapefile", "Shapefile 無法解析為 FeatureCollection。");
}

function polygons(geometry) {
  if (geometry?.type === "Polygon") return [geometry.coordinates];
  if (geometry?.type === "MultiPolygon") return geometry.coordinates;
  throw new BuildUploadError("wrong-geometry", "BUILD 圖層只能包含 Polygon 或 MultiPolygon geometry。");
}

function orientation(a, b, c) {
  const value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1]);
  if (Math.abs(value) < 1e-12) return 0;
  return value > 0 ? 1 : 2;
}

function onSegment(a, b, c) {
  return (
    b[0] <= Math.max(a[0], c[0]) + 1e-12 &&
    b[0] + 1e-12 >= Math.min(a[0], c[0]) &&
    b[1] <= Math.max(a[1], c[1]) + 1e-12 &&
    b[1] + 1e-12 >= Math.min(a[1], c[1])
  );
}

function segmentsIntersect(a, b, c, d) {
  const o1 = orientation(a, b, c);
  const o2 = orientation(a, b, d);
  const o3 = orientation(c, d, a);
  const o4 = orientation(c, d, b);
  if (o1 !== o2 && o3 !== o4) return true;
  return (
    (o1 === 0 && onSegment(a, c, b)) ||
    (o2 === 0 && onSegment(a, d, b)) ||
    (o3 === 0 && onSegment(c, a, d)) ||
    (o4 === 0 && onSegment(c, b, d))
  );
}

function inspectRing(ring, featureNumber) {
  assert(Array.isArray(ring) && ring.length >= 4, "invalid-ring", `第 ${featureNumber} 筆建物含少於四個 vertex 的 ring。`);
  let hasZ = false;
  let twiceArea = 0;
  for (const [index, coordinate] of ring.entries()) {
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
    if (coordinate.length >= 3 && Number.isFinite(coordinate[2])) hasZ = true;
    if (index < ring.length - 1) {
      const next = ring[index + 1];
      twiceArea += coordinate[0] * next[1] - next[0] * coordinate[1];
    }
  }
  const first = ring[0];
  const last = ring.at(-1);
  assert(first[0] === last[0] && first[1] === last[1], "ring-not-closed", `第 ${featureNumber} 筆建物含未閉合 ring。`);
  assert(Math.abs(twiceArea) > 1e-14, "zero-area-ring", `第 ${featureNumber} 筆建物含零面積 ring。`);
  const edgeCount = ring.length - 1;
  for (let left = 0; left < edgeCount; left += 1) {
    for (let right = left + 1; right < edgeCount; right += 1) {
      if (right === left + 1 || (left === 0 && right === edgeCount - 1)) continue;
      assert(
        !segmentsIntersect(ring[left], ring[left + 1], ring[right], ring[right + 1]),
        "self-intersecting-ring",
        `第 ${featureNumber} 筆建物含自相交 ring；資料檢查已終止。`,
      );
    }
  }
  return {vertexCount: ring.length, hasZ};
}

function inspectGeometry(geometry, featureNumber) {
  let vertexCount = 0;
  let ringCount = 0;
  let hasZ = false;
  for (const polygon of polygons(geometry)) {
    assert(Array.isArray(polygon) && polygon.length > 0, "empty-polygon", `第 ${featureNumber} 筆建物沒有 polygon ring。`);
    for (const ring of polygon) {
      const inspected = inspectRing(ring, featureNumber);
      vertexCount += inspected.vertexCount;
      ringCount += 1;
      hasZ ||= inspected.hasZ;
    }
  }
  return {vertexCount, ringCount, hasZ};
}

function validActor(value) {
  return /^[A-Za-z0-9._:@-]{1,120}$/.test(value || "");
}

export function inspectBuildFeatures(parsed, archive, options = {}) {
  const input = normalizedFeatureCollection(parsed);
  const features = input.features;
  assert(Array.isArray(features) && features.length > 0, "no-features", "Shapefile 沒有圖徵。");
  assert(
    features.length <= BUILD_UPLOAD_LIMITS.featureCount,
    "too-many-features",
    `單一 BUILD 圖層最多接受 ${BUILD_UPLOAD_LIMITS.featureCount.toLocaleString()} 筆面圖徵。`,
  );
  const collection = structuredClone(input);
  const rawCounts = {};
  const identities = new Set();
  const vertexCounts = [];
  const ringCounts = [];
  let totalVertexCount = 0;
  let totalRingCount = 0;
  let multipartFeatureCount = 0;
  let zFeatureCount = 0;
  let annotatedFeatureCount = 0;
  for (const [index, feature] of collection.features.entries()) {
    const number = index + 1;
    const properties = feature?.properties;
    assert(properties && typeof properties === "object", "properties-missing", `第 ${number} 筆缺少屬性。`);
    for (const field of BUILD_SCHEMA_FIELDS) {
      assert(Object.hasOwn(properties, field), "required-field-missing", `缺少必要欄位 ${field}；資料檢查已終止。`);
    }
    assert(
      feature.geometry?.type === "Polygon" || feature.geometry?.type === "MultiPolygon",
      "wrong-geometry",
      "BUILD 圖層只能包含 Polygon 或 MultiPolygon geometry。",
    );
    const geometry = inspectGeometry(feature.geometry, number);
    totalVertexCount += geometry.vertexCount;
    totalRingCount += geometry.ringCount;
    vertexCounts.push(geometry.vertexCount);
    ringCounts.push(geometry.ringCount);
    if (feature.geometry.type === "MultiPolygon") multipartFeatureCount += 1;
    if (geometry.hasZ) zFeatureCount += 1;
    assert(
      totalVertexCount <= BUILD_UPLOAD_LIMITS.vertexCount,
      "too-many-vertices",
      `BUILD 圖層最多接受 ${BUILD_UPLOAD_LIMITS.vertexCount.toLocaleString()} 個 vertices。`,
    );
    const sourceId = String(properties.BUILD_ID ?? "").trim();
    assert(sourceId, "empty-build-id", `第 ${number} 筆 BUILD_ID 是空白。`);
    const identity = `${archive.zipRelativeBase}::${sourceId}`;
    assert(!identities.has(identity), "duplicate-identity", `filename + BUILD_ID 不唯一：${identity}。`);
    identities.add(identity);
    const code = String(properties.TERRAINID ?? "").trim();
    assert(
      Object.hasOwn(BUILD_CODES, code),
      "invalid-build-classification",
      `第 ${number} 筆 TERRAINID=${code || "(空白)"} 不在目前已審查的 BUILD polygon 分類範圍。`,
    );
    rawCounts[code] = (rawCounts[code] || 0) + 1;
    if (String(properties.BUILD_NO ?? "").trim() || String(properties.BUILD_STR ?? "").trim()) {
      annotatedFeatureCount += 1;
    }
  }

  const clarifications = [];
  for (const sourceCode of Object.keys(rawCounts).filter((code) => BUILD_PARENT_OPTIONS[code])) {
    const effectiveCode = options.parentResolutions?.[sourceCode];
    if (!Object.hasOwn(BUILD_PARENT_OPTIONS[sourceCode], effectiveCode || "")) {
      clarifications.push({
        type: "parent-classification",
        sourceCode,
        sourceName: BUILD_CODES[sourceCode],
        count: rawCounts[sourceCode],
        options: BUILD_PARENT_OPTIONS[sourceCode],
        question: `${sourceCode} 是建物父分類；這 ${rawCounts[sourceCode]} 筆資料實際屬於哪一個附件七細類？`,
      });
    }
  }
  if (clarifications.length) {
    return {
      status: "clarification-required",
      collection,
      rawCounts,
      clarifications,
      preliminary: {featureCount: features.length, totalVertexCount, totalRingCount},
    };
  }

  const resolutions = [];
  const counts = {};
  for (const feature of collection.features) {
    const sourceCode = String(feature.properties.TERRAINID).trim();
    const effectiveCode = options.parentResolutions?.[sourceCode] || sourceCode;
    feature.properties.__NMA_BUILD_CLASS = effectiveCode;
    counts[effectiveCode] = (counts[effectiveCode] || 0) + 1;
  }
  for (const sourceCode of Object.keys(rawCounts).filter((code) => BUILD_PARENT_OPTIONS[code])) {
    assert(
      validActor(options.parentResolutionConfirmedBy),
      "classification-reviewer-invalid",
      "請提供本次父分類釐清的審查者識別。",
    );
    resolutions.push({
      source_code: sourceCode,
      effective_code: options.parentResolutions[sourceCode],
      status: "session-human-confirmed",
      confirmed_by: options.parentResolutionConfirmedBy,
    });
  }
  return {
    status: "ready",
    collection,
    observation: {
      sourceLayer: "BUILD",
      geometryFamily: "polygon",
      geometryTypes: [...new Set(collection.features.map((feature) => feature.geometry.type))].sort(),
      schemaProfile: {
        id: "multidimensional-build-v4",
        status: "reviewed-versioned-source-schema",
        fields: [...BUILD_SCHEMA_FIELDS],
      },
      classificationField: "TERRAINID",
      identityField: "BUILD_ID",
      annotationFields: ["BUILD_NO", "BUILD_STR"],
      observedClassCounts: counts,
      classificationResolutions: resolutions,
      featureCount: features.length,
      totalVertexCount,
      totalRingCount,
      vertexCounts,
      ringCounts,
      multipartFeatureCount,
      zFeatureCount,
      annotatedFeatureCount,
      sourceIdentityRule: "zip-relative-filename-plus-source-id",
      outputCrs: "EPSG:4326",
      sourceDimension: zFeatureCount === features.length ? "XYZ" : zFeatureCount ? "mixed-XY-XYZ" : "XY",
      rawFeatureBytesTransmitted: false,
    },
  };
}
