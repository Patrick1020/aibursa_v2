from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_list_prediction():
    r = client.post("/api/predictions", json={"ticker": "AAPL", "horizon_days": 7})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ticker"] == "AAPL"
    r2 = client.get("/api/predictions")
    assert r2.status_code == 200
    arr = r2.json()
    assert any(x["id"] == data["id"] for x in arr)
