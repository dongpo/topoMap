import fs from "node:fs";

import {
  RoadUploadError,
  inspectRoadFeatures,
  validateRoadArchive,
} from "../assets/js/nma-road-upload-v1.js";
import {listZipEntries} from "../assets/js/nma-school-upload-v1.js";

const archivePath = process.argv[2];
const mode = process.argv[3] || "direct";
const bytes = fs.readFileSync(archivePath);
const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);

try {
  const archive = validateRoadArchive(
    {name: archivePath.split("/").at(-1), size: bytes.byteLength},
    listZipEntries(buffer),
  );
  const codes = mode === "parent" ? ["9420100"] : ["9420101", "9420400", "9420700", "9420802"];
  const featureCollection = {
    type: "FeatureCollection",
    features: codes.map((code, index) => ({
      type: "Feature",
      properties: {
        ROADSEGID: `R-${index + 1}`,
        TERRAINID: code,
        ROADNAME: index === 1 ? "中山街" : `道路 ${index + 1}`,
        ROADNUM: index === 1 ? "縣126" : "",
        ROADNUM1: "",
        ROADNUM2: "",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [121 + index / 100, 24 + index / 100],
          [121.005 + index / 100, 24.004 + index / 100],
          [121.01 + index / 100, 24.006 + index / 100],
        ],
      },
    })),
  };
  const first = inspectRoadFeatures(featureCollection, archive);
  if (mode === "parent") {
    process.stdout.write(
      JSON.stringify({
        status: first.status,
        clarificationTypes: first.clarifications.map((item) => item.type),
        parentOptions: Object.keys(first.clarifications.at(-1).options),
      }),
    );
  } else {
    const ready = inspectRoadFeatures(featureCollection, archive, {
      schemaMappingConfirmedBy: "browser-reviewer",
      parentResolutions: {},
    });
    process.stdout.write(
      JSON.stringify({
        status: ready.status,
        layerName: archive.layerName,
        featureCount: ready.observation.featureCount,
        totalVertexCount: ready.observation.totalVertexCount,
        vertexCounts: ready.observation.vertexCounts,
        classCounts: ready.observation.observedClassCounts,
        mappingStatus: ready.observation.classificationFieldMapping.status,
        rawFeatureBytesTransmitted: ready.observation.rawFeatureBytesTransmitted,
      }),
    );
  }
} catch (error) {
  if (!(error instanceof RoadUploadError)) throw error;
  process.stdout.write(JSON.stringify({status: "rejected", code: error.code, message: error.message}));
}
