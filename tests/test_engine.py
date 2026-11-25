"""Unit tests for the pure business logic (no Flask, no database)."""
import pytest

from backend.seed_data import CARDS
from backend.services import engine
from backend.services.presenter import compact, fee_text, inr

CARD = {c["id"]: c for c in CARDS}


def test_interest_matches_reference_site():
    r = engine.interest(50000, 42, 12, 5000)
    assert r["monthly_rate_pct"] == 3.5
    assert r["interest_paid"] == 12544
    assert r["still_owed"] == 2544


def test_interest_cleared_early_and_zero_rate():
    r = engine.interest(10000, 0, 12, 5000)
    assert r["interest_paid"] == 0 and r["cleared"] and len(r["schedule"]) == 2


def test_interest_payment_too_low_flagged():
    r = engine.interest(100000, 36, 6, 1000)  # monthly interest is 3000
    assert r["never_reduces"] is True and r["still_owed"] > 100000


@pytest.mark.parametrize("bad", [(0, 10, 12, 100), (1000, -1, 12, 100), (1000, 10, 0, 100), ("x", 10, 12, 100)])
def test_interest_rejects_bad_input(bad):
    with pytest.raises(engine.ValidationError):
        engine.interest(*bad)


def test_cashback_millennia_online():
    r = engine.cashback(CARD["hdfc-millennia"], "online_shopping", 10000, 0)
    assert (r["rate_pct"], r["per_month"], r["per_year"]) == (5.0, 500.0, 6000.0)


def test_cashback_respects_cap_and_falls_back_to_base_rate():
    assert engine.cashback(CARD["hdfc-millennia"], "online_shopping", 100000, 750)["per_month"] == 750
    assert engine.cashback(CARD["hdfc-millennia"], "dining", 10000, 0)["rate_pct"] == 1.0


def test_category_reward_caps_bonus_only():
    card = CARD["axis-ace"]
    capped = engine.category_reward(card, "dining", 100000)
    assert capped == pytest.approx(500 + 100000 * 0.4 * 0.015)


def test_fuel_surcharge_saving_capped():
    assert engine.fuel_surcharge_saving(CARD["sbi-cashback"], 3000) == 360
    assert engine.fuel_surcharge_saving(CARD["sbi-cashback"], 100000) == 1200
    assert engine.fuel_surcharge_saving(CARD["axis-atlas"], 3000) == 0


def test_fee_waiver_applied_when_spend_reaches_threshold():
    card = CARD["sbi-cashback"]
    assert engine.effective_annual_fee(card, 199999) == 999
    assert engine.effective_annual_fee(card, 200000) == 0


def test_validate_profile_cleans_and_rejects(profile):
    clean = engine.validate_profile(profile)
    assert clean["salary"] == 80000.0 and clean["name"] == "akshay"
    profile["expenses"]["fuel"] = -5
    profile["lifestyle"] = "nope"
    with pytest.raises(engine.ValidationError) as exc:
        engine.validate_profile(profile)
    assert "expenses.fuel" in exc.value.errors and "lifestyle" in exc.value.errors


def test_recommend_ranks_filters_and_excludes_fd(profile):
    profile = engine.validate_profile(profile)
    matches, filtered = engine.recommend(profile, CARDS)
    assert len(matches) == 3
    assert [m["rank"] for m in matches] == [1, 2, 3]
    nets = [m["score"] for m in matches]
    assert nets == sorted(nets, reverse=True)
    assert all(not m["card"]["is_fd_backed"] for m in matches)
    assert any(f["id"] == "icici-emeralde-private" for f in filtered)  # fee 12,499 > 5,000


def test_recommend_filters_low_income(profile):
    profile["salary"] = 10000
    matches, filtered = engine.recommend(engine.validate_profile(profile), CARDS, top_n=20)
    assert all(m["card"]["min_income"] <= 10000 for m in matches)
    assert any(f["reason"] == "Below minimum income" for f in filtered)


def test_lounge_value_only_for_frequent_traveller(profile):
    traveller = engine.evaluate_card(CARD["hdfc-millennia"], engine.validate_profile(profile))
    profile["lifestyle"] = "foodie"
    other = engine.evaluate_card(CARD["hdfc-millennia"], engine.validate_profile(profile))
    assert traveller["lounge_value"] > 0 and other["lounge_value"] == 0


def test_fd_options_eligibility_and_limit():
    cards = [c for c in CARDS if c["is_fd_backed"]]
    out = engine.fd_options(cards, 50000)
    assert all(o["eligible"] for o in out)
    assert out[0]["credit_limit"] == 50000  # IDFC WOW: 100% of FD
    low = engine.fd_options(cards, 12000)
    assert [o["eligible"] for o in low].count(True) == 1
    assert low[0]["card"]["id"] == "kotak-811-fd" and low[0]["credit_limit"] == 10800


def test_presenter_formatting():
    assert inr(1234567) == "₹12,34,567" and inr(999) == "₹999" and inr(50000) == "₹50,000"
    assert compact(200000) == "₹2L" and compact(50000) == "₹50K"
    assert fee_text(CARD["sbi-cashback"]) == "Joining ₹999 · Annual ₹999 (Waived on ₹2L annual spend)"
    assert fee_text(CARD["kotak-811-fd"]) == "Joining Free · Annual Free (Lifetime free)"
