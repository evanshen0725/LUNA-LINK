# Data integration notes

## 1. JPL Horizons

The backend requests observer ephemerides for the Sun (`10`) and Earth (`399`) from a user-defined lunar surface coordinate. The request uses the Moon body ID `301`, geodetic coordinates, and observer-table quantity codes `4,20` (apparent azimuth/elevation; observer range/range-rate).

Before scientific use, verify:
- east longitude convention and valid range;
- lunar mean-Earth frame / DE421 compatibility with the DEM being used;
- altitude convention (km above the reference ellipsoid);
- target-specific output columns and units;
- time scale and output cadence;
- whether a returned geometric elevation is being compared with a geometric or terrain horizon.

JPL Horizons reference: https://ssd-api.jpl.nasa.gov/doc/horizons.html

## 2. Moon Trek WMTS

Moon Trek exposes map services through OGC WMTS. For a proper map client:
1. Open the official Moon Trek WMTS catalog.
2. Choose the South Pole service and inspect its GetCapabilities XML.
3. Read the exact layer identifier, style identifier, TileMatrixSet, TileMatrix IDs, bounding box, and resource URL template.
4. Configure an OGC WMTS client with those values; do not infer or fabricate tile paths.

Catalog: https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=moon

## 3. LOLA DEM

The south-pole products include surface-interpolated elevation (LDEM), slope, LOLA count (LDEC), and uncertainty rasters. Several site-specific products are 5 m/pixel GeoTIFFs with south-polar stereographic X/Y coordinates and a Moon mean-Earth / DE421 reference frame. Preserve this metadata when transforming coordinates or sampling terrain.

Dataset: https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/

The full regional mosaic can be multi-gigabyte. Do not download it automatically on application startup; use a user-managed data directory and a manifest.

## 4. QuickMap and CSA

QuickMap is treated as a research/viewing destination. CSA Moon Exploration is treated as mission context and partner information. Neither is represented here as a documented machine-readable API.

## 5. Implemented LOLA GeoTIFF processing

- `POST /api/dem/upload` accepts a GeoTIFF into `data/` and returns raster metadata.
- `GET /api/dem/catalog` lists local rasters.
- `GET /api/dem/inspect?filename=...` returns CRS, bounds, pixel size and elevation statistics.
- `GET /api/dem/horizon?...` samples radial rays from an observer coordinate and estimates a horizon angle per azimuth.
- `POST /api/dem/visibility` compares supplied ephemeris azimuth/elevation samples with the terrain horizon.

Use the official site-specific LOLA products when possible. The regional 5 m products are stereographic X/Y metres in MOON_ME / DE421; do not feed latitude/longitude into the DEM horizon endpoint. The observer X/Y must be in the exact raster CRS. The azimuths from Horizons must also be transformed to the DEM grid-north convention (including polar map convergence) before visibility comparison. This release reports the azimuth reference explicitly and does not silently apply a guessed rotation.

## 6. WMTS capabilities discovery

`GET /api/wmts/capabilities?url=<encoded-https-GetCapabilities-URL>` retrieves and parses official Trek WMTS capabilities, returning layer identifiers, formats, resource URL templates, TileMatrixSet IDs and supported CRS. Use the exact GetCapabilities URL exposed by the selected service in the official Moon Trek catalog. The endpoint intentionally does not guess layer names or tile paths. The current release provides service discovery/metadata integration; an in-app tile renderer for lunar polar stereographic CRSs is not claimed as complete. A renderer must register the exact lunar CRS and tile matrix geometry from the selected service, or reproject tiles.

## 7. NSGA-II Pareto baseline

`POST /api/optimization/pareto` accepts a list of already measured candidates with `id`, `sunlight_pct`, `communication_pct`, and `slope_deg`. It runs a discrete candidate-selection NSGA-II baseline to identify non-dominated trade-offs. It does not optimize arbitrary map coordinates and does not replace landing hazard certification. Candidate metrics must use the same mission interval, height, DEM, reference frame and ephemeris assumptions.
