import fs from "node:fs";

import {
  BuildUploadError,
  inspectBuildFeatures,
  validateBuildArchive,
} from "../assets/js/nma-build-upload-v1.js";
import {listZipEntries} from "../assets/js/nma-school-upload-v1.js";

const archivePath = process.argv[2];
const mode = process.argv[3] || "direct";
const bytes = fs.readFileSync(archivePath);
const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);

try {
  const archive = validateBuildArchive(
    {name: archivePath.split("/").at(-1), size: bytes.byteLength},
    listZipEntries(buffer),
  );
  const codes = mode === "parent" ? ["9310000"] : ["9310100", "9310103", "9310200", "9310300"];
  const featureCollection = {
    type: "FeatureCollection",
    features: codes.map((code, index) => ({
      type: "Feature",
      properties: {
        BUILD_ID: `B-${index + 1}`,
        TERRAINID: code,
        BUILD_STR: code === "9310100" ? "RC" : "",
        BUILD_NO: code === "9310100" ? 3 : null,
        BUILD_H: 9.5,
        GROUP_ID: `G-${index + 1}`,
        MDATE: "20260825",
      },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [121 + index / 100, 24, 2],
          [121.006 + index / 100, 24, 2],
          [121.006 + index / 100, 24.005, 2],
          [121 + index / 100, 24.005, 2],
          [121 + index / 100, 24, 2],
        ]],
      },
    })),
  };
  const inspected = inspectBuildFeatures(featureCollection, archive);
  if (mode === "parent") {
    process.stdout.write(JSON.stringify({
      status: inspected.status,
      clarificationTypes: inspected.clarifications.map((item) => item.type),
      parentOptions: Object.keys(inspected.clarifications[0].options),
    }));
  } else {
    process.stdout.write(JSON.stringify({
      status: inspected.status,
      layerName: archive.layerName,
      featureCount: inspected.observation.featureCount,
      totalVertexCount: inspected.observation.totalVertexCount,
      totalRingCount: inspected.observation.totalRingCount,
      vertexCounts: inspected.observation.vertexCounts,
      zFeatureCount: inspected.observation.zFeatureCount,
      classCounts: inspected.observation.observedClassCounts,
      schemaProfile: inspected.observation.schemaProfile.id,
      rawFeatureBytesTransmitted: inspected.observation.rawFeatureBytesTransmitted,
    }));
  }
} catch (error) {
  if (!(error instanceof BuildUploadError)) throw error;
  process.stdout.write(JSON.stringify({status: "rejected", code: error.code, message: error.message}));
}
