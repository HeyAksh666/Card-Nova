"""SQLite access layer: connection handling, schema and seeding."""
import json
import os
import sqlite3

from flask import current_app, g

from .seed_data import CARDS

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    data       TEXT    NOT NULL,
    updated_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cards (
    id                   TEXT PRIMARY KEY,
    bank                 TEXT    NOT NULL,
    name                 TEXT    NOT NULL,
    tier                 TEXT    NOT NULL,
    joining_fee          INTEGER NOT NULL DEFAULT 0,
    annual_fee           INTEGER NOT NULL DEFAULT 0,
    fee_waiver_spend     INTEGER,
    fee_note             TEXT,
    base_rate            REAL    NOT NULL DEFAULT 0,
    rates                TEXT    NOT NULL DEFAULT '{}',
    fuel                 TEXT,
    lounge_domestic      INTEGER NOT NULL DEFAULT 0,
    lounge_international INTEGER NOT NULL DEFAULT 0,
    lifestyles           TEXT    NOT NULL DEFAULT '[]',
    highlights           TEXT    NOT NULL DEFAULT '[]',
    min_income           INTEGER NOT NULL DEFAULT 0,
    is_fd_backed         INTEGER NOT NULL DEFAULT 0,
    fd_min               INTEGER,
    fd_limit_pct         REAL,
    apply_url            TEXT    NOT NULL,
    theme                TEXT    NOT NULL DEFAULT 'slate'
);
CREATE TABLE IF NOT EXISTS recommendation_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    salary      REAL    NOT NULL,
    lifestyle   TEXT    NOT NULL,
    top_card_id TEXT    REFERENCES cards(id),
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cards_bank ON cards(bank);
"""

JSON_COLUMNS = ("rates", "fuel", "lifestyles", "highlights")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def seed_cards(db, reset=False):
    if reset:
        db.execute("DELETE FROM cards")
    if db.execute("SELECT COUNT(*) FROM cards").fetchone()[0] > 0:
        return
    for card in CARDS:
        row = dict(card)
        for col in JSON_COLUMNS:
            row[col] = json.dumps(row[col])
        cols = ", ".join(row)
        marks = ", ".join(":" + k for k in row)
        db.execute(f"INSERT INTO cards ({cols}) VALUES ({marks})", row)
    db.commit()


def init_db(app, reset=False):
    path = app.config["DATABASE"]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        seed_cards(db, reset=reset)
    app.teardown_appcontext(close_db)
