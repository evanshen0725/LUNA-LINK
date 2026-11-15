# LUNA-LINK v0.3 — Orbital Mission Control

**Lunar South-Pole Mission Intelligence & 3D Visualization Prototype**

LUNA-LINK is an independent student research prototype for exploring lunar south-pole candidate sites. It combines a Three.js/WebGL mission-control interface with a FastAPI service for LOLA GeoTIFF inspection, DEM terrain-horizon sampling, JPL Horizons observer queries, WMTS capability discovery, and a discrete-candidate NSGA-II Pareto baseline.

> **Scientific integrity notice:** This is not flight software and must not be used for real mission decisions. The default 3D Moon, crater relief, site pins, telemetry and timeline are illustrative/procedural. They are not NASA observations. NASA/JPL/ASU/CSA do not endorse this project. A live data provider connection does not by itself validate coordinate frames, time scales, instrument products or scientific interpretation.

## 1. Features

### 3D frontend
- Three.js lunar globe with procedural crater relief, star field, Earth and Sun direction cues.
- OrbitControls: rotate, zoom, auto-rotate, reset and fullscreen.
- Mission Control, Terrain Lab and Optimization views.
- Candidate-site selection, telemetry panels and a 24-hour illustrative visibility timeline.
- Optimization request to the FastAPI backend.
- Responsive dark mission-control interface.

### Backend
- `GET /api/health` — service health.
- `GET /api/sites` — illustrative candidate-site catalogue.
- `GET /api/horizons/observer` — JPL Horizons observer ephemeris proxy.
- `GET /api/trek/catalog` — NASA Trek WMTS discovery guidance; does not invent a tile endpoint.
- `GET /api/resources` — source catalogue.
- `POST /api/dem/upload` — upload and inspect a GeoTIFF.
- `GET /api/dem/catalog` — list uploaded DEMs.
- `GET /api/dem/inspect` — inspect a DEM by filename.
- `GET /api/dem/heightmap` — downsample and normalize a GeoTIFF DEM into an elevation grid for 3D Three.js mesh rendering.
- `GET /api/dem/horizon` — sample terrain horizon by azimuth in the DEM's native CRS.
- `POST /api/dem/visibility` — compare supplied ephemeris azimuth/elevation with terrain horizon.
- `POST /api/optimization/pareto` — discrete-candidate NSGA-II baseline.
- `GET /docs` — interactive OpenAPI documentation.

## 2. Requirements
- Python 3.10+
- Modern browser with WebGL2
- Internet access for Three.js modules and Google Fonts loaded from CDNs
- Rasterio/GDAL for GeoTIFF operations (installed through `requirements.txt`; platform-specific GDAL wheels may vary)

## 3. Windows quick start

Double-click `start_windows.bat`. It creates a virtual environment, installs dependencies, starts the frontend at port 5500 and the API at port 8000.

Then open:
- Frontend: <http://127.0.0.1:5500>
- API docs: <http://127.0.0.1:8000/docs>

## 4. Manual start (Windows/macOS/Linux)

Terminal 1:

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd frontend
python -m http.server 5500
```

Open <http://127.0.0.1:5500>.

## 5. Using a LOLA DEM

1. Obtain a suitable LOLA GeoTIFF from the NASA/GSFC Planetary Geodesy and Data Archive (PGDA) or another documented provider.
2. Confirm its product documentation, vertical units, map projection, body-fixed reference frame, longitude convention, and epoch/frame realization.
3. Open <http://127.0.0.1:8000/docs> and use `POST /api/dem/upload` to upload the `.tif`/`.tiff` file.
4. Inspect the returned CRS, bounds, pixel size, units and tags.
5. Use `GET /api/dem/horizon` with `x` and `y` in the **native projected CRS coordinates of that exact raster**, not latitude/longitude.
6. Compare ephemeris only after converting the Horizons direction into the same local azimuth convention and correcting polar-stereographic map convergence.

The horizon routine estimates geometric terrain obstruction by ray sampling. It does not yet model diffraction, refraction, finite solar/Earth disk, boulder-scale hazards, rover/antenna height, or a full radio link budget.

## 6. NSGA-II API example

`POST /api/optimization/pareto` accepts evaluated candidate metrics. Example body:

```json
{
  "candidates": [
    {"id":"A", "sunlight_pct":88, "communication_pct":92, "slope_deg":5.2},
    {"id":"B", "sunlight_pct":95, "communication_pct":70, "slope_deg":3.1},
    {"id":"C", "sunlight_pct":76, "communication_pct":98, "slope_deg":7.0}
  ],
  "population_size":80,
  "generations":80,
  "seed":7
}
```

This is a **discrete candidate baseline**: NSGA-II selects among supplied evaluated candidates. It is not continuous global optimization over the lunar surface. Results are only as scientifically meaningful as the input metrics and their common time window, coordinate frame and assumptions.

## 7. NASA Trek / WMTS integration

Do not hard-code guessed tile URLs. Discover the correct Moon/South Pole service, layer identifier, style, tile format, TileMatrixSet and matrix identifiers from the official Trek service documentation and its live GetCapabilities response. A generic Earth Web Mercator viewer is not automatically compatible with lunar polar-stereographic products. The current release provides the discovery/API entry point but does **not** claim that live NASA Trek tiles are already rendered in the 3D globe.

## 8. Test

From the project root:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The included unit tests cover the DEM helper logic and NSGA-II baseline. They do not validate NASA data provenance or mission-grade coordinate transformations.

## 9. Data sources and attribution

- NASA/GSFC PGDA LOLA products: <https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/>
- NASA Moon Trek: <https://trek.nasa.gov/moon/>
- NASA/JPL Horizons: <https://ssd.jpl.nasa.gov/horizons/>
- LROC QuickMap (ASU): <https://quickmap.lroc.asu.edu/>
- Canadian Space Agency Moon Exploration: <https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/>

Follow each provider's current access, attribution and reuse terms. NASA does not endorse non-U.S. Government entities or third-party websites.

## 10. Current limitations / next research milestones

1. Render a verified NASA Trek lunar-polar WMTS layer using its exact projection and matrix metadata.
2. Convert a verified LOLA DEM window into a GPU displacement/mesh representation and stream it to Three.js.
3. Establish and test a complete lunar body-fixed / inertial / local-horizon coordinate transformation pipeline for Horizons output.
4. Model Sun and Earth finite angular disks, terrain obstruction and time-dependent visibility consistently.
5. Compute candidate metrics directly from measured DEM and ephemeris data before feeding NSGA-II.
6. Add uncertainty propagation, sensitivity analysis and reproducible experiment exports.

---

**Project status:** Advanced visualization prototype + research backend foundation. Live NASA data ingestion and mission-grade validation remain explicit integration tasks, not completed claims.
