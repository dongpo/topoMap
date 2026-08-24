export const SCHOOL_UPLOAD_LIMITS = Object.freeze({
  archiveBytes: 16 * 1024 * 1024,
  uncompressedBytes: 128 * 1024 * 1024,
  entryCount: 64,
  featureCount: 50_000,
});

export const SCHOOL_CODES = Object.freeze({
  "9920101": "大專院校",
  "9920102": "中學",
  "9920103": "小學",
  "9920104": "職訓中心",
  "9920105": "幼兒園",
  "9920106": "特殊學校",
});

const REQUIRED_COMPONENTS = Object.freeze([".shp", ".shx", ".dbf", ".prj"]);
const OPTIONAL_COMPONENTS = Object.freeze([".cpg"]);
const ZIP_EOCD = 0x06054b50;
const ZIP_CENTRAL_FILE = 0x02014b50;

export class SchoolUploadError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "SchoolUploadError";
    this.code = code;
  }
}

function assert(condition, code, message) {
  if (!condition) throw new SchoolUploadError(code, message);
}

function safeEntryName(value) {
  const normalized = value.replaceAll("\\", "/").replace(/^\.\//, "");
  assert(
    normalized && !normalized.startsWith("/") && !normalized.split("/").includes(".."),
    "unsafe-archive-path",
    "ZIP 含有不安全的檔案路徑。",
  );
  return normalized;
}

function findEndOfCentralDirectory(view) {
  const lowerBound = Math.max(0, view.byteLength - 65_557);
  for (let offset = view.byteLength - 22; offset >= lowerBound; offset -= 1) {
    if (view.getUint32(offset, true) === ZIP_EOCD) return offset;
  }
  throw new SchoolUploadError("invalid-zip", "找不到有效的 ZIP central directory。");
}

export function listZipEntries(arrayBuffer) {
  assert(arrayBuffer instanceof ArrayBuffer, "invalid-zip", "ZIP 內容無法讀取。");
  const view = new DataView(arrayBuffer);
  assert(view.byteLength >= 22, "invalid-zip", "ZIP 檔案不完整。");
  const eocd = findEndOfCentralDirectory(view);
  const diskNumber = view.getUint16(eocd + 4, true);
  const centralDisk = view.getUint16(eocd + 6, true);
  const entryCount = view.getUint16(eocd + 10, true);
  const centralSize = view.getUint32(eocd + 12, true);
  const centralOffset = view.getUint32(eocd + 16, true);
  assert(diskNumber === 0 && centralDisk === 0, "multi-disk-zip", "不支援 multi-disk ZIP。");
  assert(
    entryCount <= SCHOOL_UPLOAD_LIMITS.entryCount,
    "too-many-entries",
    `ZIP 最多可包含 ${SCHOOL_UPLOAD_LIMITS.entryCount} 個項目。`,
  );
  assert(
    centralOffset + centralSize <= view.byteLength,
    "invalid-zip",
    "ZIP central directory 超出檔案範圍。",
  );

  const decoder = new TextDecoder("utf-8", {fatal: false});
  const entries = [];
  let offset = centralOffset;
  let totalUncompressed = 0;
  for (let index = 0; index < entryCount; index += 1) {
    assert(
      offset + 46 <= view.byteLength && view.getUint32(offset, true) === ZIP_CENTRAL_FILE,
      "invalid-zip",
      "ZIP central directory record 無效。",
    );
    const flags = view.getUint16(offset + 8, true);
    const method = view.getUint16(offset + 10, true);
    const compressedSize = view.getUint32(offset + 20, true);
    const uncompressedSize = view.getUint32(offset + 24, true);
    const filenameLength = view.getUint16(offset + 28, true);
    const extraLength = view.getUint16(offset + 30, true);
    const commentLength = view.getUint16(offset + 32, true);
    const end = offset + 46 + filenameLength + extraLength + commentLength;
    assert(end <= view.byteLength, "invalid-zip", "ZIP entry record 不完整。");
    assert((flags & 1) === 0, "encrypted-zip", "不支援加密 ZIP。");
    assert(method === 0 || method === 8, "unsupported-compression", "ZIP 使用不支援的壓縮方法。");
    const rawName = new Uint8Array(arrayBuffer, offset + 46, filenameLength);
    const name = safeEntryName(decoder.decode(rawName));
    totalUncompressed += uncompressedSize;
    assert(
      totalUncompressed <= SCHOOL_UPLOAD_LIMITS.uncompressedBytes,
      "archive-expands-too-large",
      "ZIP 解壓後內容超過 128 MiB 限制。",
    );
    if (compressedSize > 0) {
      assert(
        uncompressedSize / compressedSize <= 1_000,
        "suspicious-compression-ratio",
        "ZIP entry 壓縮比例異常。",
      );
    }
    entries.push({name, lowerName: name.toLowerCase(), compressedSize, uncompressedSize});
    offset = end;
  }
  return entries;
}

function componentExtension(name) {
  const match = name.toLowerCase().match(/\.(shp|shx|dbf|prj|cpg)$/);
  return match ? `.${match[1]}` : null;
}

export function validateSchoolArchive(file, entries) {
  assert(file?.name?.toLowerCase().endsWith(".zip"), "zip-required", "請上傳 `.zip` 檔案。");
  assert(file.size > 0, "empty-archive", "ZIP 檔案是空的。");
  assert(
    file.size <= SCHOOL_UPLOAD_LIMITS.archiveBytes,
    "archive-too-large",
    "ZIP 超過 16 MiB；此限制略高於已檢視的 12,822,898-byte 基準資料。",
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
  assert(groups.size === 1, "multiple-shapefiles", "School demo 每次只接受一個 Shapefile 圖層。");
  const [[base, components]] = groups.entries();
  const missing = REQUIRED_COMPONENTS.filter((extension) => !components.has(extension));
  assert(
    missing.length === 0,
    "required-component-missing",
    `缺少必要元件：${missing.join("、")}。`,
  );
  const layerName = base.split("/").at(-1);
  assert(
    layerName === "mark" || layerName.endsWith("_mark"),
    "mark-layer-required",
    "School demo 只接受 MARK 點圖層（檔名需為 MARK 或 *_MARK）。",
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
  throw new SchoolUploadError("invalid-shapefile", "Shapefile 無法解析為 FeatureCollection。");
}

export function inspectSchoolFeatures(parsed, archive) {
  const collection = normalizedFeatureCollection(parsed);
  const features = collection.features;
  assert(Array.isArray(features) && features.length > 0, "no-features", "Shapefile 沒有圖徵。");
  assert(
    features.length <= SCHOOL_UPLOAD_LIMITS.featureCount,
    "too-many-features",
    `單一 School 圖層最多接受 ${SCHOOL_UPLOAD_LIMITS.featureCount.toLocaleString()} 個點。`,
  );
  const counts = {};
  const identities = new Set();
  for (const [index, feature] of features.entries()) {
    const properties = feature?.properties;
    assert(properties && typeof properties === "object", "properties-missing", `第 ${index + 1} 筆缺少屬性。`);
    for (const field of ["MARKID", "TERRAINID", "MARKNAME1"]) {
      assert(
        Object.hasOwn(properties, field),
        "required-field-missing",
        `缺少必要欄位 ${field}；資料檢查已終止。`,
      );
    }
    assert(feature.geometry?.type === "Point", "wrong-geometry", "School MARK 必須全部是 Point geometry。");
    const coordinates = feature.geometry.coordinates;
    assert(
      Array.isArray(coordinates) &&
        coordinates.length >= 2 &&
        Number.isFinite(coordinates[0]) &&
        Number.isFinite(coordinates[1]) &&
        coordinates[0] >= -180 &&
        coordinates[0] <= 180 &&
        coordinates[1] >= -90 &&
        coordinates[1] <= 90,
      "crs-transform-failed",
      "座標未成功轉換為 WGS84；請檢查 `.prj` 是否正確。",
    );
    const code = String(properties.TERRAINID ?? "").trim();
    assert(
      Object.hasOwn(SCHOOL_CODES, code),
      "invalid-terrainid",
      `第 ${index + 1} 筆 TERRAINID=${code || "(空白)"} 不是 9920101–9920106。`,
    );
    const sourceId = String(properties.MARKID ?? "").trim();
    assert(sourceId, "empty-markid", `第 ${index + 1} 筆 MARKID 是空白。`);
    const identity = `${archive.zipRelativeBase}::${sourceId}`;
    assert(!identities.has(identity), "duplicate-identity", `filename + MARKID 不唯一：${identity}。`);
    identities.add(identity);
    assert(
      String(properties.MARKNAME1 ?? "").trim(),
      "empty-markname1",
      `第 ${index + 1} 筆 MARKNAME1 是空白，無法依規則註記名稱。`,
    );
    counts[code] = (counts[code] || 0) + 1;
  }
  return {
    collection,
    observation: {
      sourceLayer: "MARK",
      geometryType: "Point",
      classificationField: "TERRAINID",
      identityField: "MARKID",
      labelField: "MARKNAME1",
      featureCount: features.length,
      observedClassCounts: counts,
      sourceIdentityRule: "zip-relative-filename-plus-source-id",
      outputCrs: "EPSG:4326",
      rawFeatureBytesTransmitted: false,
    },
  };
}

export async function sha256Hex(arrayBuffer) {
  const digest = await crypto.subtle.digest("SHA-256", arrayBuffer);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}
