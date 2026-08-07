#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");
const { execFileSync } = require("node:child_process");

function loadQrRuntime() {
  const candidates = ["qrcode-terminal/vendor/QRCode"];
  try {
    const globalRoot = execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim();
    candidates.push(path.join(globalRoot, "npm/node_modules/qrcode-terminal/vendor/QRCode"));
  } catch (_) {
    // The regular module lookup below may still succeed.
  }

  for (const candidate of candidates) {
    try {
      const QRCode = require(candidate);
      const base = path.dirname(require.resolve(candidate));
      const levels = require(path.join(base, "QRErrorCorrectLevel"));
      return { QRCode, levels };
    } catch (_) {
      // Continue to the next known npm layout.
    }
  }
  throw new Error("qrcode-terminal runtime not found; install npm before regenerating D24 assets");
}

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const typeBuffer = Buffer.from(type, "ascii");
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const checksum = Buffer.alloc(4);
  checksum.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])));
  return Buffer.concat([length, typeBuffer, data, checksum]);
}

function encodePng(matrix, output, scale = 12, quietModules = 4) {
  const modules = matrix.length + quietModules * 2;
  const size = modules * scale;
  const rows = [];

  for (let y = 0; y < size; y += 1) {
    const row = Buffer.alloc(size + 1, 255);
    row[0] = 0;
    const moduleY = Math.floor(y / scale) - quietModules;
    for (let x = 0; x < size; x += 1) {
      const moduleX = Math.floor(x / scale) - quietModules;
      if (
        moduleY >= 0 &&
        moduleY < matrix.length &&
        moduleX >= 0 &&
        moduleX < matrix.length &&
        matrix[moduleY][moduleX]
      ) {
        row[x + 1] = 0;
      }
    }
    rows.push(row);
  }

  const header = Buffer.alloc(13);
  header.writeUInt32BE(size, 0);
  header.writeUInt32BE(size, 4);
  header[8] = 8;
  header[9] = 0;

  const png = Buffer.concat([
    Buffer.from("89504e470d0a1a0a", "hex"),
    pngChunk("IHDR", header),
    pngChunk("IDAT", zlib.deflateSync(Buffer.concat(rows), { level: 9 })),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);

  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, png);
}

function main() {
  const [, , payload, output] = process.argv;
  if (!payload || !output) {
    throw new Error("usage: generate_d24_qr.js URL OUTPUT.png");
  }

  const { QRCode, levels } = loadQrRuntime();
  const qr = new QRCode(-1, levels.M);
  qr.addData(payload);
  qr.make();
  encodePng(qr.modules, output);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 2;
}
