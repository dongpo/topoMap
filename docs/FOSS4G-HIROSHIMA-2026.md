# FOSS4G Hiroshima 2026 demonstration plan

Accepted talk: **National Map Agent: An Open Geospatial Architecture for Knowledge Graph–Driven
GeoAI**.

FOSS4G Hiroshima runs 30 August-5 September 2026; the main conference is 1-3 September and the
community sprint is 4 September. Official information:

- <https://2026.foss4g.org/en/>
- <https://2026.foss4g.org/en/program-schedule/community-sprint/>

## Claim to demonstrate

National-mapping specifications can be operationalized as open, inspectable rules that an agent can
retrieve and execute through deterministic FOSS4G tooling, while preserving evidence and human
authority.

The talk does not claim autonomous authoritative production.

## Eight-minute live sequence

1. Show the official RIVERL table on page 39 and GIS-quality rules on page 22.
2. Open the controlled `RIVERL.shp` containing four known defects.
3. Run `nma demo` and show GDAL/OGR reporting the driver, CRS, field widths, and feature count.
4. Display the map and the four localized issues: missing ID, undocumented code, self-intersection,
   and full-width excess spaces.
5. Open an issue to show the exact document, version, section, page, source URL, expected value, and
   observed value.
6. Request repair. Show that identity, classification, and geometry remain proposals requiring
   expert judgment.
7. Approve only whitespace normalization, revalidate, and show the audit record.
8. Finish with the 31-task benchmark, open repository, and community-sprint extension path.

Keep a recorded terminal session and the generated HTML report as fallback. Never depend on live
model or external-network availability for the core proof.

## FOSS4G alignment

| Principle | Implemented evidence |
|---|---|
| Free/open source | Apache-2.0 code, public tests, Docker, CI |
| Geospatial execution | GDAL/OGR Shapefile inspection and feature reading with engine provenance |
| Reproducible data | synthetic Shapefiles regenerated from transparent CSV/VRT sources |
| Interoperability | Shapefile, GeoJSON, JSON Schema, OpenAPI, CLI, HTTP JSON |
| Inspectability | deterministic validators and page-level rule evidence |
| Community extension | new country/layer profiles require data and rule files, not framework adoption |
| Responsible openness | official PDFs and private archive referenced but not redistributed |

## Audience evidence package

- one-command local/container reproduction;
- pre-generated HTML before/after reports;
- `benchmark/ground-truth.json` and complete task set;
- machine-generated results with source fingerprints;
- exact source-page manifest;
- architecture and research-protocol documents;
- candidate `RIVERID`/`RIVERLID` discrepancy clearly marked pending review.

## Community sprint backlog

1. Add a QGIS Processing provider for the same validation contract.
2. Add GeoPackage and PostGIS multi-layer topology checks.
3. Add an OGC API Processes or pygeoapi adapter.
4. Contribute another national feature catalogue/profile.
5. Review rules and translations with domain experts.
6. Expand the sealed benchmark and run named open-model baselines.
