import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

import pytest

from app import app, init_db


@pytest.fixture
def client():
    app.config["TESTING"] = True

    init_db()

    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "running"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"


def test_create_task_without_title(client):
    response = client.post(
        "/tasks",
        json={
            "description": "Task without title"
        }
    )

    assert response.status_code == 400


def test_get_non_existing_task(client):
    response = client.get("/tasks/999999")

    assert response.status_code == 404


def test_create_task(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Test Task",
            "description": "Created by pytest",
            "status": "pending"
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["task"]["title"] == "Test Task"
    assert data["task"]["status"] == "pending"


def test_get_tasks(client):
    response = client.get("/tasks")

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)
