# LUNA-LINK v0.3 — Orbital Mission Control

An advanced Three.js visualization frontend layered onto the LUNA-LINK v0.2 FastAPI scientific-data backend.

## Highlights
- Full-screen Three.js lunar globe with procedural crater relief, orbit path, star field, Earth target, directional solar lighting and animated telemetry overlays.
- OrbitControls: drag to rotate, scroll to zoom, auto-rotation toggle, reset and zoom controls.
- Mission control, terrain lab and optimization navigation states.
- Candidate-site selection synchronized with coordinates, telemetry cards and 24-hour visibility chart.
- Layer toggles for relief preview, orbit, solar vector and Earth line-of-sight vector.
- Backend health check and real `/api/optimization/pareto` invocation using the v0.2 API schema.
- Responsive mission-control layout and fullscreen mode.

## Run
Use Python 3.10+.

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
python -m http.server 5500
```

Open http://127.0.0.1:5500 . Use a modern browser with WebGL2 and internet access because Three.js and Google Fonts are loaded from CDNs.

On Windows, `start_windows.bat` starts the backend and frontend server.

## Scientific integrity / limitations
- The current globe's albedo and crater rings are **procedural visualization assets**, not actual LOLA DEM terrain. The interface explicitly labels the environment as a simulation/prototype. Do not present the procedural craters as NASA observations.
- The site coordinates and initial telemetry are illustrative placeholders inherited from the prototype. They are not verified landing coordinates or flight recommendations.
- Earth range, angular diameter and chart curves shown in the UI are illustrative until a live Horizons response is fetched, parsed, transformed into the correct lunar local frame and validated.
- The line-of-sight vector is a visual cue, not a radio-frequency link budget or a validated topographic occultation result.
- The Pareto button calls the backend NSGA-II discrete-candidate endpoint with demonstration metrics. A Pareto result is only as scientifically valid as the input metrics.
- WMTS capability discovery and DEM analysis remain backend capabilities; this release does not yet render NASA Trek WMTS tiles or transform a real LOLA GeoTIFF into a GPU terrain mesh.

## Next engineering milestone
1. Parse a verified NASA Trek GetCapabilities document and render its actual tile matrix in a polar-stereographic-aware map view.
2. Load a LOLA GeoTIFF in the backend, reproject/resample a selected area into a mesh/height texture and stream it to Three.js.
3. Replace the procedural moon material with a real lunar basemap and terrain-derived normal/displacement maps.
4. Integrate Horizons observer ephemerides in a documented coordinate/time frame and animate Sun/Earth from those returned vectors.
5. Replace illustrative candidate metrics with measured illumination, terrain horizon and visibility metrics over a common time window.

## Attribution
LUNA-LINK is an independent student prototype. NASA, JPL, ASU and CSA do not endorse this project. Respect each data provider's license, attribution and usage terms. NASA imagery/data should be attributed to its originating mission/instrument where required.
