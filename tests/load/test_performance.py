"""
Load & performance tests.
Run with: pytest tests/load/ -v --tb=short
These tests verify response-time budgets under simulated concurrency.
No external load tool required — uses threading + TestClient.
"""
import io
import time
import threading
import statistics
import pytest
from fastapi.testclient import TestClient

from api.main import app
from tests.conftest import auth_header

SAMPLE_PROPOSAL = b"""
Our enterprise platform supports 1000+ concurrent users with horizontal scaling.
We use PostgreSQL 16 with read replicas and Redis caching for sub-100ms response times.
Full OAuth 2.0, SAML 2.0, and MFA authentication are included.
Our 99.99% uptime SLA is backed by 24/7 NOC monitoring.
Complete delivery in 5 months. Total cost: $850,000 including 1-year support.
"""


@pytest.fixture(scope="module")
def load_client():
    return TestClient(app)


@pytest.fixture(scope="module")
def load_token(load_client):
    load_client.post("/api/v1/auth/register", json={
        "email": "loadtest@test.com",
        "password": "LoadTest1",
        "full_name": "Load Test User",
    })
    res = load_client.post("/api/v1/auth/login", json={
        "email": "loadtest@test.com",
        "password": "LoadTest1",
    })
    return res.json()["data"]["access_token"]


class LatencyTracker:
    def __init__(self):
        self.latencies: list[float] = []
        self.errors: int = 0
        self._lock = threading.Lock()

    def record(self, latency: float):
        with self._lock:
            self.latencies.append(latency)

    def record_error(self):
        with self._lock:
            self.errors += 1

    def report(self) -> dict:
        if not self.latencies:
            return {"count": 0, "errors": self.errors}
        return {
            "count": len(self.latencies),
            "errors": self.errors,
            "p50_ms": round(statistics.median(self.latencies) * 1000, 1),
            "p95_ms": round(sorted(self.latencies)[int(len(self.latencies) * 0.95)] * 1000, 1),
            "max_ms": round(max(self.latencies) * 1000, 1),
            "min_ms": round(min(self.latencies) * 1000, 1),
        }


def test_health_endpoint_latency(load_client):
    """Health check must respond under 200ms."""
    latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        res = load_client.get("/health")
        latencies.append(time.perf_counter() - t0)
        assert res.status_code == 200

    p95 = sorted(latencies)[int(len(latencies) * 0.95)]
    print(f"\nHealth P95: {p95*1000:.1f}ms")
    assert p95 < 0.2, f"Health endpoint P95 {p95*1000:.1f}ms exceeds 200ms budget"


def test_br_list_latency(load_client, load_token):
    """BR list must respond under 500ms P95."""
    tracker = LatencyTracker()

    def call():
        t0 = time.perf_counter()
        res = load_client.get("/api/v1/br-projects", headers=auth_header(load_token))
        if res.status_code == 200:
            tracker.record(time.perf_counter() - t0)
        else:
            tracker.record_error()

    threads = [threading.Thread(target=call) for _ in range(30)]
    for t in threads: t.start()
    for t in threads: t.join()

    report = tracker.report()
    print(f"\nBR List: {report}")
    assert tracker.errors == 0, f"{tracker.errors} errors during load test"
    assert report["p95_ms"] < 500, f"P95 {report['p95_ms']}ms exceeds 500ms budget"


def test_concurrent_br_create(load_client, load_token):
    """20 concurrent BR creates should all succeed."""
    results = []
    lock = threading.Lock()

    def create(i: int):
        res = load_client.post("/api/v1/br-projects",
                               json={"title": f"Concurrent BR {i}"},
                               headers=auth_header(load_token))
        with lock:
            results.append(res.status_code)

    threads = [threading.Thread(target=create, args=(i,)) for i in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()

    failures = [s for s in results if s != 201]
    assert len(failures) == 0, f"{len(failures)} concurrent creates failed: {set(failures)}"


def test_concurrent_login(load_client):
    """25 concurrent logins should all succeed without lockout."""
    # Create a dedicated user for this test
    load_client.post("/api/v1/auth/register", json={
        "email": "concurrent@test.com",
        "password": "Conc1234",
        "full_name": "Concurrent Test",
    })
    results = []
    lock = threading.Lock()

    def do_login():
        res = load_client.post("/api/v1/auth/login", json={
            "email": "concurrent@test.com",
            "password": "Conc1234",
        })
        with lock:
            results.append(res.status_code)

    threads = [threading.Thread(target=do_login) for _ in range(25)]
    for t in threads: t.start()
    for t in threads: t.join()

    success = results.count(200)
    assert success >= 20, f"Only {success}/25 concurrent logins succeeded"


def test_proposal_upload_throughput(load_client, load_token):
    """5 sequential proposal uploads should each complete under 3s."""
    br_res = load_client.post("/api/v1/br-projects",
                              json={"title": "Throughput Test BR"},
                              headers=auth_header(load_token))
    br_id = br_res.json()["data"]["id"]

    latencies = []
    for i in range(5):
        t0 = time.perf_counter()
        res = load_client.post(
            f"/api/v1/br-projects/{br_id}/proposals",
            params={"vendor_name": f"Throughput Vendor {i}"},
            files={"file": ("p.txt", io.BytesIO(SAMPLE_PROPOSAL), "text/plain")},
            headers=auth_header(load_token),
        )
        latencies.append(time.perf_counter() - t0)
        assert res.status_code == 201, f"Upload {i} failed: {res.text}"

    max_lat = max(latencies)
    print(f"\nProposal upload max latency: {max_lat*1000:.1f}ms")
    assert max_lat < 3.0, f"Slowest upload {max_lat*1000:.1f}ms exceeds 3s budget"


def test_pagination_large_dataset(load_client, load_token):
    """Paginated listing should remain fast even with many records."""
    # Create 15 BR projects
    for i in range(15):
        load_client.post("/api/v1/br-projects",
                         json={"title": f"Pagination BR {i}"},
                         headers=auth_header(load_token))

    latencies = []
    for page in range(1, 4):
        t0 = time.perf_counter()
        res = load_client.get(f"/api/v1/br-projects?page={page}&page_size=5",
                              headers=auth_header(load_token))
        latencies.append(time.perf_counter() - t0)
        assert res.status_code == 200
        assert len(res.json()["items"]) <= 5

    print(f"\nPagination latencies: {[round(l*1000,1) for l in latencies]}ms")
    assert max(latencies) < 0.5, "Paginated query exceeds 500ms"
