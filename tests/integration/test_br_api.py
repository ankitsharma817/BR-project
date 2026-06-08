"""Integration tests for BR project CRUD and requirements."""
import pytest
from tests.conftest import auth_header


# ── BR CRUD ───────────────────────────────────────────────────────────────────

def test_create_br_project(client, user_token):
    res = client.post("/api/v1/br-projects", json={
        "title": "Test BR Project",
        "description": "A test BR",
        "budget_min": 100000,
        "budget_max": 500000,
    }, headers=auth_header(user_token))
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["title"] == "Test BR Project"
    assert data["status"] == "draft"
    return data["id"]


def test_list_br_projects(client, user_token):
    # Create one first
    client.post("/api/v1/br-projects", json={"title": "List Test BR"},
                headers=auth_header(user_token))
    res = client.get("/api/v1/br-projects", headers=auth_header(user_token))
    assert res.status_code == 200
    assert "items" in res.json()
    assert res.json()["total"] >= 1


def test_get_br_project(client, user_token):
    create_res = client.post("/api/v1/br-projects", json={"title": "Get Test BR"},
                             headers=auth_header(user_token))
    br_id = create_res.json()["data"]["id"]

    res = client.get(f"/api/v1/br-projects/{br_id}", headers=auth_header(user_token))
    assert res.status_code == 200
    assert res.json()["data"]["id"] == br_id


def test_get_nonexistent_br(client, user_token):
    res = client.get("/api/v1/br-projects/00000000-0000-0000-0000-000000000000",
                     headers=auth_header(user_token))
    assert res.status_code == 404


def test_update_br_project(client, user_token):
    create_res = client.post("/api/v1/br-projects", json={"title": "Update Me"},
                             headers=auth_header(user_token))
    br_id = create_res.json()["data"]["id"]

    res = client.put(f"/api/v1/br-projects/{br_id}", json={
        "title": "Updated Title",
        "status": "active",
    }, headers=auth_header(user_token))
    assert res.status_code == 200
    assert res.json()["data"]["title"] == "Updated Title"
    assert res.json()["data"]["status"] == "active"


def test_delete_br_project(client, user_token):
    create_res = client.post("/api/v1/br-projects", json={"title": "Delete Me"},
                             headers=auth_header(user_token))
    br_id = create_res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/br-projects/{br_id}", headers=auth_header(user_token))
    assert del_res.status_code == 200

    get_res = client.get(f"/api/v1/br-projects/{br_id}", headers=auth_header(user_token))
    assert get_res.status_code == 404


# ── Requirements CRUD ─────────────────────────────────────────────────────────

@pytest.fixture
def br_id(client, user_token):
    res = client.post("/api/v1/br-projects", json={"title": "Req Test BR"},
                      headers=auth_header(user_token))
    return res.json()["data"]["id"]


def test_create_requirement(client, user_token, br_id):
    res = client.post(f"/api/v1/br-projects/{br_id}/requirements", json={
        "text": "The system must support 500 concurrent users.",
        "category": "technical",
        "priority": "critical",
    }, headers=auth_header(user_token))
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["category"] == "technical"
    assert data["priority"] == "critical"


def test_list_requirements(client, user_token, br_id):
    client.post(f"/api/v1/br-projects/{br_id}/requirements", json={
        "text": "Requirement A for listing test.",
        "category": "functional",
        "priority": "high",
    }, headers=auth_header(user_token))
    res = client.get(f"/api/v1/br-projects/{br_id}/requirements",
                     headers=auth_header(user_token))
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1


def test_update_requirement(client, user_token, br_id):
    create_res = client.post(f"/api/v1/br-projects/{br_id}/requirements", json={
        "text": "Old text that must be updated.",
        "category": "functional",
        "priority": "low",
    }, headers=auth_header(user_token))
    req_id = create_res.json()["data"]["id"]

    res = client.put(f"/api/v1/br-projects/{br_id}/requirements/{req_id}",
                     json={"priority": "critical"},
                     headers=auth_header(user_token))
    assert res.status_code == 200
    assert res.json()["data"]["priority"] == "critical"


def test_delete_requirement(client, user_token, br_id):
    create_res = client.post(f"/api/v1/br-projects/{br_id}/requirements", json={
        "text": "This requirement will be deleted.",
        "category": "functional",
        "priority": "low",
    }, headers=auth_header(user_token))
    req_id = create_res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/br-projects/{br_id}/requirements/{req_id}",
                            headers=auth_header(user_token))
    assert del_res.status_code == 200

    list_res = client.get(f"/api/v1/br-projects/{br_id}/requirements",
                          headers=auth_header(user_token))
    req_ids = [r["id"] for r in list_res.json()["data"]]
    assert req_id not in req_ids


def test_create_br_requires_auth(client):
    res = client.post("/api/v1/br-projects", json={"title": "No Auth"})
    assert res.status_code == 403
