from datetime import date
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
from .sites import SITES
from .horizons import observer_ephemeris, HorizonsError
from .config import settings

app = FastAPI(title=settings.app_name, version="0.1.0", description="Lunar south-pole exploration and mission-planning data gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status":"ok", "service":settings.app_name, "version":"0.1.0"}

@app.get("/api/sites")
def sites():
    return {"items":SITES, "notice":"Candidate coordinates are illustrative map pins, not verified landing coordinates."}

@app.get("/api/horizons/observer")
async def horizons(latitude: float = Query(..., ge=-90, le=90), longitude: float = Query(..., ge=-360, le=360),
                   start: date = Query(...), days: int = Query(1, ge=1, le=7), target: str = Query("10", pattern="^(10|399)$"), step: str = Query("1 h", pattern="^(1 h|30 m|10 m)$")):
    try:
        return await observer_ephemeris(target, latitude, longitude, start, days, step)
    except (httpx.HTTPError, HorizonsError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"JPL Horizons request failed: {exc}") from exc

@app.get("/api/trek/catalog")
async def trek_catalog():
    """Return official NASA Trek WMTS capability entry points; client can discover exact layers."""
    return {
      "provider":"NASA Solar System Treks / JPL / SSERVI",
      "documentation":"https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=moon",
      "note":"Use the Trek WMTS catalog to discover the exact South Pole GetCapabilities URL, layer IDs, matrix sets, styles and tile formats. The app intentionally does not fabricate a tile endpoint."
    }

@app.get("/api/resources")
def resources():
    return {"resources":[
      {"name":"LROC QuickMap","type":"interactive viewer","url":"https://quickmap.lroc.asu.edu/","integration":"External research/viewer link; do not assume an undocumented public API."},
      {"name":"NASA Moon Trek","type":"WMTS map services","url":"https://trek.nasa.gov/moon/","integration":"Use official Trek WMTS GetCapabilities and compatible WMTS client."},
      {"name":"JPL Horizons","type":"ephemeris API","url":"https://ssd-api.jpl.nasa.gov/doc/horizons.html","integration":"Backend proxy at /api/horizons/observer."},
      {"name":"LOLA South Pole DEMs","type":"GeoTIFF datasets","url":"https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/","integration":"Download GeoTIFFs separately; process with Rasterio/GDAL."},
      {"name":"CSA Moon Exploration","type":"mission context","url":"https://www.asc-csa.gc.ca/eng/astronomy/moon-exploration/","integration":"Reference and attribution; not a geospatial API."}
    ]}

# --- Advanced research modules: LOLA DEM, terrain horizon, WMTS discovery, NSGA-II ---
from pathlib import Path
from tempfile import gettempdir
from fastapi import UploadFile, File
from fastapi.responses import Response
from .dem import inspect_dem, terrain_horizon, DEMError, visibility_check
from .pareto import optimize_sites
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/api/dem/upload")
async def upload_dem(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".tif", ".tiff")):
        raise HTTPException(status_code=400, detail="Upload a GeoTIFF (.tif/.tiff) file")
    # Keep only a safe basename and cap upload size at 1.5 GB.
    name = Path(file.filename).name
    dest = DATA_DIR / name
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 1_500_000_000:
                    raise HTTPException(status_code=413, detail="GeoTIFF exceeds 1.5 GB upload limit")
                out.write(chunk)
        metadata = inspect_dem(str(dest))
        metadata["path"] = str(dest)
        return metadata
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

@app.get("/api/dem/catalog")
def dem_catalog():
    files = []
    for p in sorted(DATA_DIR.glob("*.tif")) + sorted(DATA_DIR.glob("*.tiff")):
        try: files.append(inspect_dem(str(p)))
        except Exception as exc: files.append({"filename": p.name, "error": str(exc)})
    return {"directory": str(DATA_DIR), "items": files,
            "official_products": "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/",
            "note": "The 5 m/pixel products use south-polar stereographic X/Y metres in MOON_ME / DE421. Confirm metadata before analysis."}

@app.get("/api/dem/inspect")
def dem_inspect(filename: str = Query(..., min_length=1)):
    p = (DATA_DIR / Path(filename).name).resolve()
    if p.parent != DATA_DIR.resolve(): raise HTTPException(status_code=400, detail="Invalid filename")
    try: return inspect_dem(str(p))
    except DEMError as exc: raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/dem/horizon")
def dem_horizon(filename: str = Query(...), x: float = Query(...), y: float = Query(...),
                max_distance_m: float = Query(5000, gt=0, le=20000), step_m: float = Query(20, gt=0, le=500),
                azimuth_step_deg: int = Query(5, ge=1, le=30)):
    p = (DATA_DIR / Path(filename).name).resolve()
    if p.parent != DATA_DIR.resolve(): raise HTTPException(status_code=400, detail="Invalid filename")
    try: return terrain_horizon(str(p), x, y, list(range(0,360,azimuth_step_deg)), max_distance_m, step_m)
    except DEMError as exc: raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/dem/visibility")
def dem_visibility(payload: dict):
    try:
        return {"results": visibility_check(payload["ephemeris"], payload["horizon_profile"], float(payload.get("margin_deg",0)))}
    except (KeyError, TypeError, ValueError, DEMError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/optimization/pareto")
def pareto(payload: dict):
    try:
        return optimize_sites(payload["candidates"], int(payload.get("population_size",80)), int(payload.get("generations",80)), int(payload.get("seed",7)))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/wmts/capabilities")
async def wmts_capabilities(url: str = Query(..., description="Exact NASA Trek WMTS GetCapabilities URL")):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith("trek.nasa.gov"):
        raise HTTPException(status_code=400, detail="Only HTTPS URLs hosted on trek.nasa.gov are accepted")
    if "request=getcapabilities" not in url.lower() and "request%3dgetcapabilities" not in url.lower():
        raise HTTPException(status_code=400, detail="URL must be an OGC WMTS GetCapabilities request")
    try:
        async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
            response = await client.get(url); response.raise_for_status()
        root = ET.fromstring(response.content)
        def local(tag): return tag.split("}")[-1]
        layers=[]; matrix_sets=[]
        for el in root.iter():
            if local(el.tag)=="Layer":
                item={}
                for ch in el:
                    if local(ch.tag)=="Identifier": item["id"]=(ch.text or "").strip()
                    elif local(ch.tag)=="Title": item["title"]=(ch.text or "").strip()
                    elif local(ch.tag)=="Format": item.setdefault("formats",[]).append((ch.text or "").strip())
                    elif local(ch.tag)=="ResourceURL": item.setdefault("resource_urls",[]).append(dict(ch.attrib))
                if item.get("id"): layers.append(item)
            elif local(el.tag)=="TileMatrixSet":
                item={}
                for ch in el:
                    if local(ch.tag)=="Identifier": item["id"]=(ch.text or "").strip()
                    elif local(ch.tag)=="SupportedCRS": item["crs"]=(ch.text or "").strip()
                if item.get("id"): matrix_sets.append(item)
        return {"source":url,"layers":layers,"tile_matrix_sets":matrix_sets,
                "note":"Use the ResourceURL template and matching TileMatrixSet/CRS. South-polar stereographic tiles cannot be overlaid as ordinary Web Mercator without reprojection."}
    except (httpx.HTTPError, ET.ParseError) as exc:
        raise HTTPException(status_code=502, detail=f"WMTS capabilities retrieval/parse failed: {exc}")
