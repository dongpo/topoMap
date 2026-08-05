# Data and evidence boundary

The repository separates authoritative source evidence from redistributable benchmark fixtures.

- `specifications/taiwan-5000-riverl-112.json` is a bounded executable interpretation of cited
  official pages. It is not a replacement for the source documents and remains pending expert
  sign-off.
- `datasets/authoritative/` contains synthetic Shapefiles whose schemas and controlled defects are
  derived from those cited rules. They contain no copied production features.
- `fixtures-source/` contains the transparent CSV/VRT source used to regenerate the Shapefiles with
  GDAL/OGR.
- The user-provided 112-year multidimensional SHP archive was inspected read-only and is not
  redistributed. Its checksum and the observed `RIVERID`/`RIVERLID` discrepancy are recorded in
  `sources/authoritative-sources.json` and `benchmark/ground-truth.json`.

Regenerate the public Shapefiles with:

```bash
for profile in riverl-clean riverl-defective riverl-schema-mismatch riverl-wrong-crs; do
  mkdir -p "data/datasets/authoritative/$profile"
  ogr2ogr -overwrite -f "ESRI Shapefile" \
    "data/datasets/authoritative/$profile" \
    "data/fixtures-source/$profile/RIVERL.vrt" \
    -lco ENCODING=UTF-8
done
```

The fixture coordinates are synthetic. Do not infer real-world hydrology or production-data
quality from them.

## D20 five-scene review dataset

The portable D20 review package has a versioned asset catalogue covering the five-scene demo
contract, ten reviewed observations, executable portrayal profile, compiled graph, MapLibre
layers, open symbol implementations, schemas, benchmark inputs, licences, and release exclusions.
See [`release/review-package/DATASET.md`](../release/review-package/DATASET.md).

The package excludes `out1120902.pmtiles` while redistribution terms remain unconfirmed and
references the official portrayal PDF without redistributing it. Its verifier reproduces the five
frozen decisions and two abstention controls without claiming browser-map or publication release.
