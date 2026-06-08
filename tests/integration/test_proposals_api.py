"""Integration tests for proposal upload and retrieval."""
import io
import pytest
from tests.conftest import auth_header

SAMPLE_TXT = b"""
Vendor Proposal: Our solution supports 500+ concurrent users with auto-scaling.
We use PostgreSQL 16 with full ACID compliance and connection pooling.
OAuth 2.0 and SAML authentication are both supported out of the box.
Our uptime SLA is 99.95% backed by a dedicated support team.
We propose delivery within 5 months with milestone-based billing.
Total cost: $750,000 including 12 months of post-deployment support.
"""


@pytest.fixture
def br_with_req(client, user_token):
    br_res = client.post("/api/v1/br-projects", json={"title": "Proposal Test BR"},
                         headers=auth_header(user_token))
    br_id = br_res.json()["data"]["id"]
    client.post(f"/api/v1/br-projects/{br_id}/requirements", json={
        "text": "System must support 500+ concurrent users.",
        "category": "technical",
        "priority": "critical",
    }, headers=auth_header(user_token))
    return br_id


def test_upload_proposal(client, user_token, br_with_req):
    res = client.post(
        f"/api/v1/br-projects/{br_with_req}/proposals",
        params={"vendor_name": "Acme Corp", "proposed_cost": "750000", "proposed_timeline_months": "5"},
        files={"file": ("proposal.txt", io.BytesIO(SAMPLE_TXT), "text/plain")},
        headers=auth_header(user_token),
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["vendor_name"] == "Acme Corp"
    assert data["status"] in ("processing", "matched")
    return data["id"]


def test_list_proposals(client, user_token, br_with_req):
    # Upload one first
    client.post(
        f"/api/v1/br-projects/{br_with_req}/proposals",
        params={"vendor_name": "List Corp"},
        files={"file": ("p.txt", io.BytesIO(SAMPLE_TXT), "text/plain")},
        headers=auth_header(user_token),
    )
    res = client.get(f"/api/v1/br-projects/{br_with_req}/proposals",
                     headers=auth_header(user_token))
    assert res.status_code == 200
    assert res.json()["total"] >= 1


def test_get_proposal(client, user_token, br_with_req):
    up_res = client.post(
        f"/api/v1/br-projects/{br_with_req}/proposals",
        params={"vendor_name": "Get Corp"},
        files={"file": ("p.txt", io.BytesIO(SAMPLE_TXT), "text/plain")},
        headers=auth_header(user_token),
    )
    pid = up_res.json()["data"]["id"]
    res = client.get(f"/api/v1/br-projects/{br_with_req}/proposals/{pid}",
                     headers=auth_header(user_token))
    assert res.status_code == 200
    assert res.json()["data"]["id"] == pid


def test_delete_proposal(client, user_token, br_with_req):
    up_res = client.post(
        f"/api/v1/br-projects/{br_with_req}/proposals",
        params={"vendor_name": "Delete Corp"},
        files={"file": ("p.txt", io.BytesIO(SAMPLE_TXT), "text/plain")},
        headers=auth_header(user_token),
    )
    pid = up_res.json()["data"]["id"]
    del_res = client.delete(f"/api/v1/br-projects/{br_with_req}/proposals/{pid}",
                            headers=auth_header(user_token))
    assert del_res.status_code == 200

    get_res = client.get(f"/api/v1/br-projects/{br_with_req}/proposals/{pid}",
                         headers=auth_header(user_token))
    assert get_res.status_code == 404


def test_upload_proposal_no_file(client, user_token, br_with_req):
    res = client.post(
        f"/api/v1/br-projects/{br_with_req}/proposals",
        params={"vendor_name": "No File Corp"},
        headers=auth_header(user_token),
    )
    assert res.status_code == 422


def test_upload_invalid_file_type(client, user_token, br_with_req):
    res = client.post(
        f"/api/v1/br-projects/{br_with_req}/proposals",
        params={"vendor_name": "Bad File Corp"},
        files={"file": ("file.exe", io.BytesIO(b"binary"), "application/octet-stream")},
        headers=auth_header(user_token),
    )
    assert res.status_code == 422
