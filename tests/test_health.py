from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

def test_get_project_name():
    response = client.get("/")
    message = response.json()["message"]

    assert response.status_code == status.HTTP_200_OK
    assert message == "Team Task Manager API"


def test_check_health():
    response = client.get("/api/v1/health/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"

