import math

from app.services.optimizer import optimize_route, haversine_km


def test_haversine_distance_basic():
    # Hyderabad to Secunderabad ~ 20 km, approx.
    distance = haversine_km(17.3850, 78.4867, 17.4399, 78.4983)
    assert 0 < distance < 50


def test_optimize_route_orders_by_distance():
    villages = [
        {"name": "A", "latitude": 17.3850, "longitude": 78.4867},
        {"name": "B", "latitude": 17.4440, "longitude": 78.4740},
        {"name": "C", "latitude": 17.3000, "longitude": 78.6000},
    ]

    result = optimize_route(villages, source_location="Hyderabad")
    ordered = [stop["name"] for stop in result["route"]]

    assert ordered[0] == "A"
    assert result["total_distance_km"] > 0
    assert result["estimated_time_hours"] > 0
    assert result["route_length"] == 3


def test_optimize_route_rejects_invalid_coordinates():
    villages = [
        {"name": "Bad", "latitude": 1000, "longitude": 78.0},
        {"name": "Good", "latitude": 17.3850, "longitude": 78.4867},
    ]

    result = optimize_route(villages, source_location="Hyderabad")
    assert result["invalid_count"] == 1
    assert any(stop["name"] == "Good" for stop in result["route"])
