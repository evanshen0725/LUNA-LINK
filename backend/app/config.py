import os

class Settings:
    app_name = os.getenv("APP_NAME", "LUNA-LINK API")
    horizons_url = os.getenv("HORIZONS_URL", "https://ssd.jpl.nasa.gov/api/horizons.api")
    request_timeout = float(os.getenv("REQUEST_TIMEOUT", "45"))

settings = Settings()
