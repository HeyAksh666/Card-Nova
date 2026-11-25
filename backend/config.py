"""Application configuration (override with environment variables)."""
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = os.environ.get("CARDNOVA_SECRET", "dev-secret-change-me")
    DATABASE = os.environ.get("CARDNOVA_DB", os.path.join(BASE_DIR, "instance", "cardnova.db"))
    TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # auth tokens live for 7 days
