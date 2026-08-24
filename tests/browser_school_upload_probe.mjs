import fs from "node:fs";

import {
  SchoolUploadError,
  inspectSchoolFeatures,
  listZipEntries,
  validateSchoolArchive,
} from "../assets/js/nma-school-upload-v1.js";

const archivePath = process.argv[2];
const bytes = fs.readFileSync(archivePath);
const arrayBuffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);

try {
  const entries = listZipEntries(arrayBuffer);
  const archive = validateSchoolArchive(
    {name: archivePath.split("/").at(-1), size: bytes.byteLength},
    entries,
  );
  const featureCollection = {
    type: "FeatureCollection",
    features: Object.keys({
      "9920101": "大專院校",
      "9920102": "中學",
      "9920103": "小學",
      "9920104": "職訓中心",
      "9920105": "幼兒園",
      "9920106": "特殊學校",
    }).map((code, index) => ({
      type: "Feature",
      properties: {MARKID: `M-${index + 1}`, TERRAINID: code, MARKNAME1: `School ${index + 1}`},
      geometry: {type: "Point", coordinates: [121 + index / 1000, 24 + index / 1000]},
    })),
  };
  const inspected = inspectSchoolFeatures(featureCollection, archive);
  process.stdout.write(
    JSON.stringify({
      status: "pass",
      layerName: archive.layerName,
      requiredComponents: archive.requiredComponents.length,
      optionalComponents: archive.optionalComponents.length,
      featureCount: inspected.observation.featureCount,
      observedClassCounts: inspected.observation.observedClassCounts,
      rawFeatureBytesTransmitted: inspected.observation.rawFeatureBytesTransmitted,
    }),
  );
} catch (error) {
  if (!(error instanceof SchoolUploadError)) throw error;
  process.stdout.write(JSON.stringify({status: "rejected", code: error.code, message: error.message}));
}
