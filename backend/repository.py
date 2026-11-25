"""Data-access functions (the only module that writes SQL)."""
import json

from .db import JSON_COLUMNS


def _row_to_card(row):
    card = dict(row)
    for col in JSON_COLUMNS:
        card[col] = json.loads(card[col]) if card[col] is not None else None
    card["is_fd_backed"] = bool(card["is_fd_backed"])
    return card


def list_cards(db, bank=None, tier=None, fd=None, q=None):
    sql, args = "SELECT * FROM cards WHERE 1=1", []
    if bank:
        sql += " AND bank = ?"
        args.append(bank)
    if tier:
        sql += " AND tier = ?"
        args.append(tier)
    if fd is not None:
        sql += " AND is_fd_backed = ?"
        args.append(1 if fd else 0)
    if q:
        sql += " AND (LOWER(name) LIKE ? OR LOWER(bank) LIKE ?)"
        args += [f"%{q.lower()}%"] * 2
    sql += " ORDER BY is_fd_backed, rowid"
    return [_row_to_card(r) for r in db.execute(sql, args).fetchall()]


def get_card(db, card_id):
    row = db.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    return _row_to_card(row) if row else None


def distinct_values(db, column):
    assert column in ("bank", "tier")
    return [r[0] for r in db.execute(f"SELECT DISTINCT {column} FROM cards ORDER BY {column}")]


def create_user(db, name, email, password_hash):
    cur = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                     (name, email, password_hash))
    db.commit()
    return cur.lastrowid


def get_user_by_email(db, email):
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user(db, user_id):
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def save_profile(db, user_id, profile):
    db.execute(
        "INSERT INTO profiles (user_id, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(user_id) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP",
        (user_id, json.dumps(profile)))
    db.commit()


def load_profile(db, user_id):
    row = db.execute("SELECT data FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    return json.loads(row["data"]) if row else None


def log_recommendation(db, user_id, profile, top_card_id):
    db.execute("INSERT INTO recommendation_log (user_id, salary, lifestyle, top_card_id) VALUES (?,?,?,?)",
               (user_id, profile["salary"], profile["lifestyle"], top_card_id))
    db.commit()
