def test_list_pagination(client, seed_legislators):
    r = client.get("/api/legislators?limit=2&offset=0&state=NY")
    assert r.status_code == 200
    data = r.get_json()
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["total"] >= 1
    assert all(item["state"] == "NY" for item in data["items"])

def test_detail_and_404(client, seed_legislators):
    r = client.get("/api/legislators/2")
    assert r.status_code == 200
    assert r.get_json()["govtrack_id"] == 2

    r2 = client.get("/api/legislators/999999")
    assert r2.status_code == 404

def test_stats_party(client, seed_legislators):
    r = client.get("/api/stats/party")
    assert r.status_code == 200
    stats = r.get_json()
    assert isinstance(stats, dict)
    assert sum(stats.values()) >= 3

def test_weather_endpoint_mocked(client, monkeypatch, seed_legislators):
    class MockResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"weather": [{"main": "Clear"}], "main": {"temp": 75}}

    import app.api.routes as routes
    monkeypatch.setattr(routes.requests, "get", lambda *a, **k: MockResp())

    r = client.get("/api/legislators/2/weather")
    assert r.status_code == 200
    out = r.get_json()
    assert "weather" in out
    assert out["legislator"]["govtrack_id"] == 2
