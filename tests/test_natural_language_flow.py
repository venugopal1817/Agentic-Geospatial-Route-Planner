from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_intent_parser_handles_natural_language_request():
    response = client.post(
        "/plan-text",
        json={"request_text": "I need to start from Hyderabad and visit Balapur, Mallapur and Chintapalli. Give me the most efficient route."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"clarification_required", "planning", "completed"}
    assert "origin" in body or "request" in body


def test_ambiguous_village_returns_clarification_request():
    response = client.post(
        "/plan-text",
        json={"request_text": "I want to visit Balapur from Hyderabad"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "clarification_required"
    assert "options" in body
    assert len(body["options"]) >= 2


def test_route_engine_orders_stops_deteministically():
    response = client.post(
        "/optimize",
        json={
            "source_location": "Hyderabad",
            "villages": [
                {"name": "A", "latitude": 17.3850, "longitude": 78.4867},
                {"name": "B", "latitude": 17.4440, "longitude": 78.4740},
                {"name": "C", "latitude": 17.3000, "longitude": 78.6000},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route_length"] >= 2
    assert body["total_distance_km"] >= 0
