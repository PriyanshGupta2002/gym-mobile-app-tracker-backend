from fastapi import APIRouter, Query

from app.schemas.location import CitiesResponse
from app.services.location import get_indian_cities

router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)


@router.get(
    "/india/cities",
    response_model=CitiesResponse,
)
async def get_indian_cities_endpoint(
    search: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    return await get_indian_cities(
        name_prefix=search,
        limit=limit,
        offset=offset,
    )
