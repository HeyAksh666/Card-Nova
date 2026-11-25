"""Optional accounts: register, login, current user, saved profile."""
import re
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from .. import repository as repo
from ..db import get_db
from ..services.engine import ValidationError, validate_profile
from . import json_error

bp = Blueprint("auth", __name__, url_prefix="/api")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="cardnova-auth")


def _public(user):
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def current_user_or_none():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        data = _serializer().loads(header[7:], max_age=current_app.config["TOKEN_MAX_AGE"])
    except (BadSignature, SignatureExpired):
        return None
    return repo.get_user(get_db(), data.get("uid"))


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user_or_none()
        if user is None:
            return json_error("Sign in required", 401)
        g.user = user
        return view(*args, **kwargs)
    return wrapper


@bp.post("/auth/register")
def register():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name") or "").strip()
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    errors = {}
    if not name:
        errors["name"] = "Name is required"
    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address"
    if len(password) < 8:
        errors["password"] = "Use at least 8 characters"
    if errors:
        return json_error("Invalid input", 400, errors)
    db = get_db()
    if repo.get_user_by_email(db, email):
        return json_error("An account with this email already exists", 409)
    uid = repo.create_user(db, name, email, generate_password_hash(password))
    token = _serializer().dumps({"uid": uid})
    return jsonify({"token": token, "user": _public(repo.get_user(db, uid))}), 201


@bp.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    user = repo.get_user_by_email(get_db(), str(body.get("email") or "").strip().lower())
    if not user or not check_password_hash(user["password_hash"], str(body.get("password") or "")):
        return json_error("Incorrect email or password", 401)
    return jsonify({"token": _serializer().dumps({"uid": user["id"]}), "user": _public(user)})


@bp.get("/auth/me")
@login_required
def me():
    return jsonify({"user": _public(g.user)})


@bp.get("/profile")
@login_required
def get_profile():
    return jsonify({"profile": repo.load_profile(get_db(), g.user["id"])})


@bp.put("/profile")
@login_required
def put_profile():
    try:
        profile = validate_profile(request.get_json(silent=True))
    except ValidationError as exc:
        return json_error("Invalid profile", 400, exc.errors)
    repo.save_profile(get_db(), g.user["id"], profile)
    return jsonify({"profile": profile})
