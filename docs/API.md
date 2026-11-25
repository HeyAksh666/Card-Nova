# Card Nova REST API

Base URL: `http://127.0.0.1:5000/api` · All bodies are JSON · Errors look like
`{"error": "message", "details": {"field": "reason"}}`.
Protected endpoints need `Authorization: Bearer <token>`.

## Catalogue

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | `{"status": "ok"}` |
| GET | `/meta` | Spend categories, lifestyles, banks, tiers |
| GET | `/cards?q=&bank=&tier=&fd=0\|1` | List cards. `fd=1` → FD-backed only |
| GET | `/cards/<id>` | One card, or 404 |

Each card includes `display.fee`, `display.fuel`, `display.lounge` (ready-to-show strings).

## Recommendation

`POST /recommend`

```json
{ "name": "akshay", "salary": 80000, "lifestyle": "frequent_traveller", "max_joining_fee": 5000,
  "expenses": { "online_shopping": 8006, "dining": 4000, "travel": 3000,
                "fuel": 3000, "groceries": 6000, "utilities": 4000 } }
```

Response → `matches` (top 3: `rank`, `card`, `rewards_year`, `fuel_saved`, `lounge_value`,
`annual_fee_paid`, `net_value`, `lifestyle_match`, `score`, `breakdown`), `filtered_out`
(cards excluded and why), and the cleaned `profile`. `400` with per-field `details` when invalid.

## FD-backed cards

`GET /fd-cards?amount=50000` → `options[]` each with `eligible`, `credit_limit`, `shortfall`.

## Calculators

`POST /calc/cashback` — `{"card_id": "hdfc-millennia", "category": "online_shopping", "monthly_spend": 10000, "monthly_cap": 0}`
→ `{"rate_pct": 5.0, "per_month": 500.0, "per_year": 6000.0, "card_cap": 1000}`

`POST /calc/interest` — `{"balance": 50000, "annual_rate": 42, "months": 12, "monthly_payment": 5000}`
→ `{"monthly_rate_pct": 3.5, "interest_paid": 12544, "still_owed": 2544, "total_paid": 60000, "cleared": false, "never_reduces": false, "schedule": [...]}`

## Accounts (optional)

| Method | Path | Body / notes |
|--------|------|--------------|
| POST | `/auth/register` | `{name, email, password (≥ 8 chars)}` → `201 {token, user}`; `409` if email exists |
| POST | `/auth/login` | `{email, password}` → `{token, user}`; `401` if wrong |
| GET | `/auth/me` | 🔒 current user |
| GET | `/profile` | 🔒 saved profile or `null` |
| PUT | `/profile` | 🔒 body as in `/recommend`; validated then stored |

## Status codes

`200` OK · `201` created · `400` validation error · `401` not signed in / bad credentials ·
`404` not found · `405` wrong method · `409` duplicate email · `500` server error.
