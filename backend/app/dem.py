"""LOLA GeoTIFF inspection and terrain-horizon analysis.

Rasterio is optional at import time; install backend requirements to enable it.
Coordinates supplied to terrain_horizon must be in the DEM's native CRS (LOLA
site products are south-polar stereographic metres, MOON_ME / DE421).
"""
from pathlib import Path
from rasterio.enums import Resampling
import math

class DEMError(RuntimeError):
    pass

def _rasterio():
    try:
        import rasterio
        return rasterio
    except ImportError as exc:
        raise DEMError("Raster support is unavailable. Install rasterio and its GDAL dependencies.") from exc

def inspect_dem(path: str):
    rio = _rasterio()
    p = Path(path)
    if not p.is_file():
        raise DEMError(f"DEM file not found: {p}")
    with rio.open(p) as ds:
        band = ds.read(1, masked=True)
        valid = band.compressed()
        if valid.size == 0:
            raise DEMError("DEM contains no valid pixels")
        return {
            "filename": p.name, "driver": ds.driver, "width": ds.width, "height": ds.height,
            "crs": str(ds.crs) if ds.crs else None, "transform": list(ds.transform)[:6],
            "bounds": [ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top],
            "pixel_size": [abs(ds.transform.a), abs(ds.transform.e)], "units": ds.units[0] if ds.units else None,
            "nodata": ds.nodata, "valid_pixels": int(valid.size),
            "elevation_m": {"min": float(valid.min()), "max": float(valid.max()), "mean": float(valid.mean()), "std": float(valid.std())},
            "tags": ds.tags(),
            "warning": "Confirm this raster is a LOLA LDEM in MOON_ME / DE421 and that supplied coordinates use this raster's native CRS."
        }

def sample_dem(path: str, x: float, y: float):
    rio = _rasterio()
    with rio.open(path) as ds:
        v = next(ds.sample([(x, y)], masked=True))[0]
        if getattr(v, "mask", False):
            return None
        try: return float(v)
        except (TypeError, ValueError): return None

def terrain_horizon(path: str, x: float, y: float, azimuths=None,
                    max_distance_m: float = 5000, step_m: float = 20):
    """Estimate local horizon elevation angle in degrees for each azimuth.

    Azimuth is clockwise from grid/north in the DEM coordinate plane. For
    polar stereographic products this is map-grid azimuth, not automatically
    lunar-north azimuth; rotate using the product's map convergence if needed.
    """
    rio = _rasterio()
    if max_distance_m <= 0 or step_m <= 0 or max_distance_m / step_m > 20000:
        raise DEMError("Invalid ray sampling distances")
    azimuths = azimuths if azimuths is not None else list(range(0, 360, 5))
    distances = [step_m * i for i in range(1, int(max_distance_m / step_m) + 1)]
    out = []
    with rio.open(path) as ds:
        origin = next(ds.sample([(x, y)], masked=True))[0]
        if getattr(origin, "mask", False): raise DEMError("Observer coordinate falls on NoData")
        z0 = float(origin)
        for az in azimuths:
            # x east, y north; azimuth clockwise from north
            a = math.radians(float(az))
            pts = [(x + d * math.sin(a), y + d * math.cos(a)) for d in distances]
            vals = list(ds.sample(pts, masked=True))
            max_angle = -90.0
            valid = 0
            for d, arr in zip(distances, vals):
                v = arr[0]
                if getattr(v, "mask", False): continue
                angle = math.degrees(math.atan2(float(v) - z0, d))
                max_angle = max(max_angle, angle); valid += 1
            out.append({"azimuth_deg": float(az), "horizon_elevation_deg": max_angle if valid else None,
                        "valid_samples": valid, "total_samples": len(distances)})
    return {"observer": {"x": x, "y": y, "elevation_m": z0}, "max_distance_m": max_distance_m,
            "step_m": step_m, "azimuth_reference": "DEM grid north; apply map-convergence correction before comparing to Horizons azimuth",
            "profile": out}

def visibility_check(ephemeris, horizon_profile, margin_deg=0.0):
    """Compare {azimuth_deg,elevation_deg} ephemerides with interpolated horizon."""
    prof = sorted([p for p in horizon_profile if p["horizon_elevation_deg"] is not None], key=lambda p:p["azimuth_deg"])
    if len(prof) < 2: raise DEMError("Insufficient terrain horizon samples")
    def horizon(az):
        az = float(az) % 360
        ext = prof + [{**prof[0], "azimuth_deg": prof[0]["azimuth_deg"] + 360}]
        for a,b in zip(ext, ext[1:]):
            aa, bb = a["azimuth_deg"], b["azimuth_deg"]
            if aa <= az <= bb or (az < ext[0]["azimuth_deg"] and aa <= az+360 <= bb):
                q = az if az >= aa else az+360
                t = (q-aa)/(bb-aa) if bb != aa else 0
                return a["horizon_elevation_deg"]*(1-t)+b["horizon_elevation_deg"]*t
        return prof[0]["horizon_elevation_deg"]
    result=[]
    for item in ephemeris:
        h=horizon(item["azimuth_deg"])
        result.append({**item,"terrain_horizon_deg":h,"terrain_visible":float(item["elevation_deg"]) > h+margin_deg})
    return result

def get_dem_heightmap(file_path: str, size: int = 128) -> dict:
    import numpy as np
    import rasterio

    with rasterio.open(file_path) as src:
        data = src.read(
            1,
            out_shape=(size, size),
            resampling=Resampling.bilinear
        ).astype("float64")

        # 過濾 NoData 以及 NASA LOLA 常見的極端無效值
        if src.nodata is not None:
            data = np.where(np.isclose(data, src.nodata), np.nan, data)
        data = np.where((data < -1e10) | (data > 1e10), np.nan, data)

        # 用有效像素的中位數填補 NaN，避免 JSON 序列化出現 NaN 報 500 錯誤
        valid_mask = ~np.isnan(data)
        if not np.any(valid_mask):
            normalized = np.zeros((size, size), dtype="float64")
            min_elev, max_elev = 0.0, 0.0
        else:
            min_elev = float(np.nanmin(data))
            max_elev = float(np.nanmax(data))
            fill_val = float(np.nanmedian(data))
            data = np.where(valid_mask, data, fill_val)

            if max_elev > min_elev:
                normalized = (data - min_elev) / (max_elev - min_elev)
            else:
                normalized = np.zeros_like(data)

        return {
            "width": size,
            "height": size,
            "min_elevation_m": min_elev,
            "max_elevation_m": max_elev,
            "grid": np.round(normalized, 4).tolist()
        }