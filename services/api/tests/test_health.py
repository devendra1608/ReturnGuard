from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_heath_endpoint_return_ok() -> None:
  response = client.get("/health")

  assert response.status_code == 200
  assert response.json() == {
    "status" : "ok",
    "service" : "returnguard-api",
  }