"""Cashback and interest calculators."""
from flask import Blueprint, jsonify, request

from .. import repository as repo
from ..db import get_db
from ..services import engine
from . import json_error

bp = Blueprint("calculators", __name__, url_prefix="/api/calc")


@bp.post("/cashback")
def cashback():
    body = request.get_json(silent=True) or {}
    card = repo.get_card(get_db(), str(body.get("card_id") or ""))
    if not card:
        return json_error("Card not found", 404)
    category = body.get("category")
    if category not in engine.CATEGORIES:
        return json_error("Unknown category", 400)
    errors = {}
    spend = engine._to_number(body.get("monthly_spend"), "monthly_spend", errors, required=True)
    cap = engine._to_number(body.get("monthly_cap"), "monthly_cap", errors)
    if errors:
        return json_error("Invalid input", 400, errors)
    return jsonify(engine.cashback(card, category, spend, cap))


@bp.post("/interest")
def interest():
    body = request.get_json(silent=True) or {}
    try:
        result = engine.interest(body.get("balance"), body.get("annual_rate"),
                                 body.get("months"), body.get("monthly_payment"))
    except engine.ValidationError as exc:
        return json_error("Invalid input", 400, exc.errors)
    return jsonify(result)
