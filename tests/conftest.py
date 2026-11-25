import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend import create_app  # noqa: E402

PROFILE = {
    "name": "akshay", "salary": 80000, "lifestyle": "frequent_traveller", "max_joining_fee": 5000,
    "expenses": {"online_shopping": 8006, "dining": 4000, "travel": 3000,
                 "fuel": 3000, "groceries": 6000, "utilities": 4000},
}


@pytest.fixture()
def app(tmp_path):
    return create_app({"DATABASE": str(tmp_path / "test.db"), "TESTING": True})


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def profile():
    return {**PROFILE, "expenses": dict(PROFILE["expenses"])}
