"""Integration tests: HTTP layer + SQLite database."""


def test_health_and_meta(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}
    meta = client.get("/api/meta").get_json()
    assert "online_shopping" in meta["categories"] and "SBI Card" in meta["banks"]


def test_cards_list_filters_and_detail(client):
    assert client.get("/api/cards").get_json()["count"] == 15
    fd = client.get("/api/cards?fd=1").get_json()
    assert fd["count"] == 5 and all(c["is_fd_backed"] for c in fd["cards"])
    sbi = client.get("/api/cards?bank=SBI Card&fd=0").get_json()
    assert {c["bank"] for c in sbi["cards"]} == {"SBI Card"}
    assert client.get("/api/cards?q=atlas").get_json()["count"] == 1
    assert client.get("/api/cards/axis-ace").get_json()["card"]["display"]["lounge"] == "None"
    assert client.get("/api/cards/unknown").status_code == 404


def test_recommend_flow(client, profile):
    body = client.post("/api/recommend", json=profile).get_json()
    assert len(body["matches"]) == 3
    top = body["matches"][0]
    assert {"rewards_year", "fuel_saved", "net_value", "rank", "breakdown"} <= set(top)
    assert top["card"]["display"]["fee"]


def test_recommend_validation_errors(client, profile):
    profile["salary"] = ""
    res = client.post("/api/recommend", json=profile)
    assert res.status_code == 400 and "salary" in res.get_json()["details"]
    assert client.post("/api/recommend", data="not json").status_code == 400


def test_calculators(client):
    r = client.post("/api/calc/interest", json={"balance": 50000, "annual_rate": 42,
                                                "months": 12, "monthly_payment": 5000}).get_json()
    assert r["interest_paid"] == 12544 and r["still_owed"] == 2544
    c = client.post("/api/calc/cashback", json={"card_id": "hdfc-millennia", "category": "online_shopping",
                                                "monthly_spend": 10000, "monthly_cap": 0}).get_json()
    assert c["per_year"] == 6000
    assert client.post("/api/calc/cashback", json={"card_id": "nope", "category": "dining",
                                                   "monthly_spend": 1}).status_code == 404
    assert client.post("/api/calc/interest", json={"balance": -1}).status_code == 400


def test_fd_cards_endpoint(client):
    body = client.get("/api/fd-cards?amount=50000").get_json()
    assert len(body["options"]) == 5 and body["options"][0]["credit_limit"] == 50000
    assert client.get("/api/fd-cards?amount=abc").status_code == 400
    assert client.get("/api/fd-cards?amount=-5").status_code == 400


def _register(client, email="a@example.com"):
    res = client.post("/api/auth/register", json={"name": "Aksh", "email": email, "password": "password123"})
    return res, {"Authorization": "Bearer " + res.get_json().get("token", "")}


def test_auth_register_login_me(client):
    res, headers = _register(client)
    assert res.status_code == 201
    assert client.get("/api/auth/me", headers=headers).get_json()["user"]["email"] == "a@example.com"
    assert client.post("/api/auth/register", json={"name": "x", "email": "a@example.com",
                                                   "password": "password123"}).status_code == 409
    ok = client.post("/api/auth/login", json={"email": "A@example.com", "password": "password123"})
    assert ok.status_code == 200 and ok.get_json()["token"]
    bad = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert bad.status_code == 401


def test_register_validation(client):
    res = client.post("/api/auth/register", json={"name": "", "email": "bad", "password": "123"})
    assert res.status_code == 400 and set(res.get_json()["details"]) == {"name", "email", "password"}


def test_profile_requires_auth_and_persists(client, profile):
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    _, headers = _register(client)
    assert client.get("/api/profile", headers=headers).get_json()["profile"] is None
    assert client.put("/api/profile", json=profile, headers=headers).status_code == 200
    saved = client.get("/api/profile", headers=headers).get_json()["profile"]
    assert saved["salary"] == 80000 and saved["expenses"]["fuel"] == 3000
    profile["salary"] = -1
    assert client.put("/api/profile", json=profile, headers=headers).status_code == 400


def test_unknown_api_route_is_json_404(client):
    res = client.get("/api/nothing")
    assert res.status_code == 404 and res.get_json()["error"] == "Not found"
