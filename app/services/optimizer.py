import math
from typing import Dict, List, Any


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between coordinates in kilometers using haversine formula."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _is_valid_coordinate(latitude: float, longitude: float) -> bool:
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def optimize_route(villages: List[Dict[str, Any]], source_location: str = "User") -> Dict[str, Any]:
    """
    Build a simple optimized route ordering for validated village locations.

    Strategy:
    - keep only valid coordinates
    - start from source and sort by nearest-neighbor distance
    - compute total distance and estimated hours
    """
    valid_villages: List[Dict[str, Any]] = []
    invalid_count = 0

    for village in villages:
        latitude = float(village.get("latitude", 0.0))
        longitude = float(village.get("longitude", 0.0))
        if not _is_valid_coordinate(latitude, longitude):
            invalid_count += 1
            continue
        valid_villages.append({
            "name": village.get("name", "Unknown"),
            "latitude": latitude,
            "longitude": longitude,
            "district": village.get("district", "Unknown"),
            "subdistric": village.get("subdistric", "Unknown"),
        })

    if not valid_villages:
        return {
            "source_location": source_location,
            "route": [],
            "total_distance_km": 0.0,
            "estimated_time_hours": 0.0,
            "route_length": 0,
            "invalid_count": invalid_count,
            "status": "no_valid_villages",
        }

    # Use source as the origin. For a simple prototype, we use the first valid village as the reference.
    # This keeps the logic deterministic and easy to test.
    current = {
        "latitude": valid_villages[0]["latitude"],
        "longitude": valid_villages[0]["longitude"],
    }

    remaining = valid_villages[1:]
    route: List[Dict[str, Any]] = [valid_villages[0]]

    while remaining:
        nearest_index = None
        nearest_distance = math.inf
        for idx, candidate in enumerate(remaining):
            d = haversine_km(
                current["latitude"],
                current["longitude"],
                candidate["latitude"],
                candidate["longitude"],
            )
            if d < nearest_distance:
                nearest_distance = d
                nearest_index = idx

        if nearest_index is None:
            break

        chosen = remaining.pop(nearest_index)
        route.append(chosen)
        current = {
            "latitude": chosen["latitude"],
            "longitude": chosen["longitude"],
        }

    total_distance = 0.0
    for i in range(len(route) - 1):
        curr = route[i]
        nxt = route[i + 1]
        total_distance += haversine_km(curr["latitude"], curr["longitude"], nxt["latitude"], nxt["longitude"])

    speed_kmh = 30.0
    estimated_time_hours = total_distance / speed_kmh

    return {
        "source_location": source_location,
        "route": route,
        "total_distance_km": round(total_distance, 2),
        "estimated_time_hours": round(estimated_time_hours, 2),
        "route_length": len(route),
        "invalid_count": invalid_count,
        "status": "optimized",
    }
