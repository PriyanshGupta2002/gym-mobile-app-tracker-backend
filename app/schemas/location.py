from pydantic import BaseModel


class CityResponse(BaseModel):
    name: str


class CitiesResponse(BaseModel):
    cities: list[CityResponse]
    total: int
    offset: int
    limit: int
