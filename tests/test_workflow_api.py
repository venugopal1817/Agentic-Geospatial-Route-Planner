from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_workflow_endpoint_returns_all_stages():
    payload = {
        "source_location": "Hyderabad",
        "villages": ["Balapur", "Mallapur", "Kothur"],
        "use_llm_summary": False,
    }

    response = client.post("/workflow", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "plan" in body
    assert "validation" in body
    assert "optimization" in body
    assert "summary" in body
    assert body["summary"]["total_requested"] == 3


def test_ui_route_serves_html_page():
    response = client.get("/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Route Planner" in response.text
