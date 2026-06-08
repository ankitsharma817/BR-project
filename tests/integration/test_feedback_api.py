"""Integration tests for feedback endpoints."""
import io
import pytest
from tests.conftest import auth_header

SAMPLE_TXT = b"Our solution supports all your requirements with 99.9% uptime SLA."


@pytest.fixture
def proposal_id(client, user_token):
    br_res = client.post("/api/v1/br-projects", json={"title": "Feedback Test BR"},
                         headers=auth_header(user_token))
    br_id = br_res.json()["data"]["id"]
    up_res = client.post(
        f"/api/v1/br-projects/{br_id}/proposals",
        params={"vendor_name": "Feedback Vendor"},
        files={"file": ("p.txt", io.BytesIO(SAMPLE_TXT), "text/plain")},
        headers=auth_header(user_token),
    )
    return up_res.json()["data"]["id"]


def test_submit_feedback(client, user_token, proposal_id):
    res = client.post(f"/api/v1/proposals/{proposal_id}/feedback", json={
        "feedback_type": "general",
        "rating": 4,
        "comment": "Good analysis overall.",
    }, headers=auth_header(user_token))
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["rating"] == 4
    assert data["feedback_type"] == "general"


def test_submit_feedback_with_score_correction(client, user_token, proposal_id):
    res = client.post(f"/api/v1/proposals/{proposal_id}/feedback", json={
        "feedback_type": "score_correction",
        "original_score": 0.75,
        "corrected_score": 0.85,
        "comment": "Score should be higher.",
    }, headers=auth_header(user_token))
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["corrected_score"] == 0.85


def test_invalid_rating_out_of_range(client, user_token, proposal_id):
    res = client.post(f"/api/v1/proposals/{proposal_id}/feedback", json={
        "feedback_type": "general",
        "rating": 6,
    }, headers=auth_header(user_token))
    assert res.status_code == 422


def test_invalid_corrected_score(client, user_token, proposal_id):
    res = client.post(f"/api/v1/proposals/{proposal_id}/feedback", json={
        "feedback_type": "score_correction",
        "corrected_score": 1.5,
    }, headers=auth_header(user_token))
    assert res.status_code == 422


def test_list_feedback(client, user_token, proposal_id):
    client.post(f"/api/v1/proposals/{proposal_id}/feedback", json={
        "feedback_type": "general", "rating": 3,
    }, headers=auth_header(user_token))
    res = client.get(f"/api/v1/proposals/{proposal_id}/feedback",
                     headers=auth_header(user_token))
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)
    assert len(res.json()["data"]) >= 1


def test_update_feedback(client, user_token, proposal_id):
    create_res = client.post(f"/api/v1/proposals/{proposal_id}/feedback", json={
        "feedback_type": "general", "rating": 2,
    }, headers=auth_header(user_token))
    fb_id = create_res.json()["data"]["id"]

    res = client.put(f"/api/v1/proposals/{proposal_id}/feedback/{fb_id}",
                     json={"rating": 5},
                     headers=auth_header(user_token))
    assert res.status_code == 200
    assert res.json()["data"]["rating"] == 5
