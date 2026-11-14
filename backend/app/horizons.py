import httpx
from datetime import date, timedelta
from .config import settings

class HorizonsError(RuntimeError):
    pass

async def observer_ephemeris(target: str, latitude: float, longitude: float,
                             start: date, days: int = 2, step: str = "1 h"):
    """Query JPL Horizons observer table from a lunar surface coordinate.

    CENTER='coord@301' selects user-specified coordinates on the Moon (301).
    SITE_COORD is longitude east, latitude, altitude in km for GEODETIC.
    Returned raw text is retained because Horizons table formats can evolve.
    """
    stop = start + timedelta(days=days)
    params = {
        "format": "json", "COMMAND": f"'{target}'", "OBJ_DATA": "NO",
        "MAKE_EPHEM": "YES", "EPHEM_TYPE": "OBSERVER",
        "CENTER": "'coord@301'", "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{longitude},{latitude},0'",
        "START_TIME": f"'{start.isoformat()}'",
        "STOP_TIME": f"'{stop.isoformat()}'", "STEP_SIZE": f"'{step}'",
        "QUANTITIES": "'4,20'", "ANG_FORMAT": "'DEG'", "CSV_FORMAT": "'YES'",
    }
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.get(settings.horizons_url, params=params)
        response.raise_for_status()
        payload = response.json()
    if payload.get("error"):
        raise HorizonsError(payload["error"])
    result = payload.get("result", "")
    if not result:
        raise HorizonsError("Horizons returned no ephemeris result")
    return {"target": target, "start": start.isoformat(), "stop": stop.isoformat(),
            "site": {"latitude": latitude, "longitude": longitude},
            "raw_result": result, "source": settings.horizons_url}
