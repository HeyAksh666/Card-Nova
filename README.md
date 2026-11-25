# Card Nova — Credit Card Recommendation Platform

A full-stack web application that recommends the best Indian credit cards for a person's real
spending, compares cards, calculates cashback and interest, and lists FD-backed cards for people
with no credit history.

* **Frontend:** HTML5, CSS3, vanilla JavaScript (ES modules, hash router) — no build step
* **Backend:** Python 3 + Flask REST API
* **Database:** SQLite (cards catalogue, users, saved profiles, recommendation log)
* **Tests:** pytest — 28 automated tests (unit + API integration)

> Card data in `backend/seed_data.py` is representative, for demonstration. Banks change fees and
> rewards often, so confirm on the bank's website before applying.

## Features

| Page | What it does |
|------|--------------|
| **My matches** | Money profile form (salary, lifestyle, max joining fee, six monthly expense categories), live card preview, and the **top 3 ranked cards** with Rewards/yr, Fuel saved, Net value and a per-category breakdown |
| **All cards** | Full catalogue with search, bank and tier filters, fee / fuel / lounge details and an "Apply" link |
| **Calculators** | **Cashback** (card × category × spend × cap) and **Interest** (balance, APR, months, payment → monthly rate, interest paid, still owed, month-by-month schedule) |
| **FD-backed cards** | Enter an FD amount; see which cards it unlocks and the credit limit you would get |
| **Account (optional)** | Register / sign in; your profile is then saved to the server and follows you across devices |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                      # open http://127.0.0.1:5000
```

Useful commands

```bash
python run.py --port 8000          # different port
python run.py --reseed             # reload the card catalogue from seed_data.py
python -m pytest -q                # run all tests
```

Environment variables: `CARDNOVA_SECRET` (token signing key — set it in production),
`CARDNOVA_DB` (path of the SQLite file, default `instance/cardnova.db`).


## Host on Streamlit Community Cloud (free)

`streamlit_app.py` is a Streamlit edition of the same project. It reuses the engine and card data,
so results are identical. (Streamlit cannot run the Flask server, so the hosted version has no
database or sign-in: the profile lives in the browser session.)

```bash
streamlit run streamlit_app.py     # local preview at http://localhost:8501
```

1. Create a GitHub repository and push this folder (`git init`, `git add .`, `git commit`, `git push`).
2. Go to https://share.streamlit.io, sign in with GitHub and choose **Create app**.
3. Pick the repository and branch, set **Main file path** to `streamlit_app.py`, then **Deploy**.
4. After a minute you get a public `*.streamlit.app` link to put in your report.

## Project structure

```
card-nova/
├── run.py                     # Flask entry point
├── streamlit_app.py           # Streamlit edition (for hosting)
├── .streamlit/config.toml     # dark/gold theme
├── requirements.txt
├── backend/
│   ├── __init__.py            # application factory (create_app), error handlers
│   ├── config.py              # settings
│   ├── db.py                  # SQLite connection, schema, seeding
│   ├── repository.py          # all SQL lives here
│   ├── seed_data.py           # card catalogue (15 cards)
│   ├── services/
│   │   ├── engine.py          # validation, reward maths, ranking, calculators (pure functions)
│   │   └── presenter.py       # ₹ formatting and display strings
│   └── routes/
│       ├── cards.py           # /api/cards, /api/recommend, /api/fd-cards, /api/meta
│       ├── calculators.py     # /api/calc/cashback, /api/calc/interest
│       └── auth.py            # /api/auth/*, /api/profile
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/                    # api.js, util.js, cardview.js, main.js (router), pages/*.js
├── tests/                     # test_engine.py (unit), test_api.py (integration)
└── docs/API.md                # REST API reference
```

Layering: **routes** (HTTP only) → **services/engine** (business rules, no I/O) → **repository** (SQL).
Because the engine is pure Python, the recommendation logic can be tested without a server.

## How a recommendation is calculated

For each non-FD card the profile can afford (joining fee ≤ your limit, salary ≥ card minimum income):

```
rewards_year   = 12 × Σ over categories ( spend × rate, bonus capped per month )
fuel_saved     = 12 × min( fuel_spend × surcharge %, monthly cap )
lounge_value   = only for "Frequent traveller": min(visits, 4 domestic / 2 international) × ₹250 / ₹600
annual_fee     = 0 if yearly spend ≥ the card's waiver threshold, else the annual fee
net_value      = rewards_year + fuel_saved + lounge_value − annual_fee
score          = net_value + ₹500 when the card suits the chosen lifestyle   (used for ranking)
```

Where a card's bonus rate only applies to some merchants (e.g. Amazon), a `share` factor limits how
much of the category earns the bonus; the rest earns the base rate.

## Security notes

* Passwords are hashed with Werkzeug (PBKDF2); tokens are signed, time-limited (7 days) with `itsdangerous`.
* All SQL uses bound parameters; all user text rendered in the browser is HTML-escaped.
* All numeric input is validated server-side (type, range, NaN/Infinity rejected).
* Not included (future work): rate limiting, HTTPS termination, password reset.

## Licence

Academic project. Bank names and trademarks belong to their owners.
