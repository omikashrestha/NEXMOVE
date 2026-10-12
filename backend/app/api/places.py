from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.app.core.places import (
    search_indian_cities,
    search_workplaces,
    calculate_intercity_distance_km
)

router = APIRouter(prefix="/api/places", tags=["Places & Workplaces"])


class CitySuggestion(BaseModel):
    name: str
    city: str
    state: str
    lat: float
    lon: float


class WorkplaceSuggestion(BaseModel):
    name: str
    workplace: str
    area: str
    category: str
    city: str


class DistanceEstimateResponse(BaseModel):
    origin_city: str
    destination_city: str
    distance_km: int


@router.get("/cities", response_model=List[CitySuggestion])
def list_cities(q: str = Query("", description="Search term for city name or state")):
    """Returns searchable Indian cities with states and geographical coordinates."""
    matches = search_indian_cities(query=q)
    return [
        CitySuggestion(
            name=c["name"],
            city=c["name"],
            state=c["state"],
            lat=c["lat"],
            lon=c["lon"]
        )
        for c in matches
    ]


@router.get("/workplaces", response_model=List[WorkplaceSuggestion])
def list_workplaces(
    city: str = Query(..., description="Target destination city"),
    q: str = Query("", description="Optional search term for workplace name or hub")
):
    """Returns major business districts, IT corridors, tech parks, and commercial hubs for a city."""
    results = search_workplaces(city_name=city, query=q)
    return [
        WorkplaceSuggestion(
            name=w["name"],
            workplace=w["name"],
            area=w["area"],
            category=w["category"],
            city=w["city"]
        )
        for w in results
    ]


@router.get("/distance", response_model=DistanceEstimateResponse)
def estimate_distance(
    origin: str = Query(..., description="Origin city"),
    destination: str = Query(..., description="Destination city")
):
    """Calculates highway road distance in km between any two Indian cities."""
    dist = calculate_intercity_distance_km(origin_city=origin, dest_city=destination)
    return DistanceEstimateResponse(
        origin_city=origin,
        destination_city=destination,
        distance_km=dist
    )
