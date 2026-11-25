"""Catalogue, recommendation and FD-card endpoints."""
from flask import Blueprint, jsonify, request

from .. import repository as repo
from ..db import get_db
from ..services import engine
from ..services.presenter import present_card
from . import json_error
from .auth import current_user_or_none

bp = Blueprint("cards", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.get("/meta")
def meta():
    db = get_db()
    return jsonify({"categories": engine.CATEGORIES, "lifestyles": engine.LIFESTYLES,
                    "banks": repo.distinct_values(db, "bank"), "tiers": repo.distinct_values(db, "tier")})


@bp.get("/cards")
def cards():
    fd = request.args.get("fd")
    fd_flag = None if fd is None else fd in ("1", "true", "yes")
    rows = repo.list_cards(get_db(), bank=request.args.get("bank"), tier=request.args.get("tier"),
                           fd=fd_flag, q=request.args.get("q"))
    return jsonify({"count": len(rows), "cards": [present_card(c) for c in rows]})


@bp.get("/cards/<card_id>")
def card_detail(card_id):
    card = repo.get_card(get_db(), card_id)
    if not card:
        return json_error("Card not found", 404)
    return jsonify({"card": present_card(card)})


@bp.post("/recommend")
def recommend():
    try:
        profile = engine.validate_profile(request.get_json(silent=True))
    except engine.ValidationError as exc:
        return json_error("Invalid profile", 400, exc.errors)
    db = get_db()
    matches, filtered = engine.recommend(profile, repo.list_cards(db, fd=False))
    for m in matches:
        m["card"] = present_card(m["card"])
    user = current_user_or_none()
    repo.log_recommendation(db, user["id"] if user else None, profile,
                            matches[0]["card"]["id"] if matches else None)
    return jsonify({"profile": profile, "matches": matches, "filtered_out": filtered})


@bp.get("/fd-cards")
def fd_cards():
    try:
        amount = float(request.args.get("amount", 0))
    except ValueError:
        return json_error("amount must be a number", 400)
    if amount < 0 or amount > engine.MAX_AMOUNT:
        return json_error("amount out of range", 400)
    options = engine.fd_options(repo.list_cards(get_db(), fd=True), amount)
    for o in options:
        o["card"] = present_card(o["card"])
    return jsonify({"amount": amount, "options": options})
