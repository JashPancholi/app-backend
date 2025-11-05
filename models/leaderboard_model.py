import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_leaderboard_fetch():
    response = client.get("/leaderboard?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    print("Leaderboard test passed ✅")
