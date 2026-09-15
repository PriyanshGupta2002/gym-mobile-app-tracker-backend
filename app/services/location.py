import httpx
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

GEODB_BASE_URL = "https://wft-geo-db.p.rapidapi.com/v1/geo"

HEADERS = {
    "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
    "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com",
}


async def get_indian_cities(
    name_prefix: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    params = {
        "countryIds": "IN",
        "limit": limit,
        "offset": offset,
        "sort": "-population",
    }

    if name_prefix:
        params["namePrefix"] = name_prefix

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{GEODB_BASE_URL}/cities",
                headers=HEADERS,
                params=params,
            )

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            logger.error(
                "GeoDB request failed: %s - %s",
                exc.response.status_code,
                exc.response.text,
            )

            raise RuntimeError("Unable to fetch cities right now.") from exc

        except httpx.RequestError as exc:
            logger.error(
                "GeoDB request failed: %s",
                str(exc),
            )

            raise RuntimeError("Unable to fetch cities right now.") from exc

        data = response.json()

    return {
        "cities": [
            {
                "name": city["city"],
            }
            for city in data.get("data", [])
        ],
        "total": data.get("metadata", {}).get("totalCount", 0),
        "offset": offset,
        "limit": limit,
    }
