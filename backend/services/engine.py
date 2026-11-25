"""Pure business logic: validation, reward maths, recommendations, calculators.

No Flask or database imports here, so every function is easy to unit-test.
All money values are in Indian rupees (Rs).
"""
import math

CATEGORIES = {
    "online_shopping": "Online shopping",
    "dining": "Dining & food delivery",
    "travel": "Travel & hotels",
    "fuel": "Fuel",
    "groceries": "Groceries",
    "utilities": "Utility bills & recharges",
}
LIFESTYLES = {
    "frequent_traveller": "Frequent traveller",
    "online_shopper": "Online shopper",
    "foodie": "Foodie",
    "daily_commuter": "Daily commuter",
    "everyday_saver": "Everyday saver",
}

MONTHS = 12
MAX_AMOUNT = 10_000_000
# Lounge assumptions: a frequent traveller is assumed to use at most this many
# visits a year, and each visit is worth this many rupees.
LOUNGE_USE = {"domestic": 4, "international": 2}
LOUNGE_VALUE = {"domestic": 250, "international": 600}
LIFESTYLE_BONUS = 500  # tie-breaker bonus (Rs) when a card suits the chosen lifestyle


class ValidationError(ValueError):
    def __init__(self, errors):
        super().__init__("Invalid input")
        self.errors = errors


def _to_number(value, field, errors, required=False, minimum=0, maximum=MAX_AMOUNT):
    if value is None or value == "":
        if required:
            errors[field] = "This field is required"
        return 0.0
    if isinstance(value, bool):
        errors[field] = "Must be a number"
        return 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors[field] = "Must be a number"
        return 0.0
    if math.isnan(number) or math.isinf(number):
        errors[field] = "Must be a finite number"
        return 0.0
    if number < minimum:
        errors[field] = f"Must be at least {minimum}"
    elif number > maximum:
        errors[field] = f"Must be at most {maximum:,}"
    return number


def validate_profile(data):
    """Return a clean profile dict or raise ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError({"_": "Expected a JSON object"})
    errors = {}
    name = str(data.get("name") or "").strip()[:26]
    salary = _to_number(data.get("salary"), "salary", errors, required=True, minimum=1)
    max_fee = _to_number(data.get("max_joining_fee"), "max_joining_fee", errors)
    lifestyle = data.get("lifestyle") or "everyday_saver"
    if lifestyle not in LIFESTYLES:
        errors["lifestyle"] = "Unknown lifestyle"
    raw = data.get("expenses") or {}
    if not isinstance(raw, dict):
        errors["expenses"] = "Expected an object"
        raw = {}
    expenses = {c: _to_number(raw.get(c), f"expenses.{c}", errors) for c in CATEGORIES}
    if errors:
        raise ValidationError(errors)
    return {"name": name, "salary": salary, "lifestyle": lifestyle,
            "max_joining_fee": max_fee, "expenses": expenses}


# ------------------------------------------------------------------ rewards
def category_reward(card, category, monthly_spend):
    """Monthly reward (Rs) a card earns on one spend category."""
    base = card["base_rate"]
    rule = card["rates"].get(category)
    if rule is None:
        return monthly_spend * base
    share = rule.get("share", 1.0)
    boosted = monthly_spend * share * rule["rate"]
    cap = rule.get("cap")
    if cap is not None:
        boosted = min(boosted, cap)
    return boosted + monthly_spend * (1 - share) * base


def fuel_surcharge_saving(card, monthly_fuel_spend):
    """Yearly fuel-surcharge waiver saving (Rs)."""
    fuel = card.get("fuel")
    if not fuel:
        return 0.0
    return min(monthly_fuel_spend * fuel["pct"], fuel["monthly_cap"]) * MONTHS


def lounge_value(card):
    dom = min(card["lounge_domestic"], LOUNGE_USE["domestic"]) * LOUNGE_VALUE["domestic"]
    intl = min(card["lounge_international"], LOUNGE_USE["international"]) * LOUNGE_VALUE["international"]
    return dom + intl


def effective_annual_fee(card, annual_spend):
    waiver = card.get("fee_waiver_spend")
    if waiver and annual_spend >= waiver:
        return 0
    return card["annual_fee"]


def evaluate_card(card, profile):
    """Yearly value of one card for one profile."""
    expenses = profile["expenses"]
    breakdown = {c: round(category_reward(card, c, s) * MONTHS, 2) for c, s in expenses.items()}
    rewards = sum(breakdown.values())
    fuel_saved = fuel_surcharge_saving(card, expenses["fuel"])
    annual_spend = sum(expenses.values()) * MONTHS
    lounges = lounge_value(card) if profile["lifestyle"] == "frequent_traveller" else 0
    fee = effective_annual_fee(card, annual_spend)
    net = rewards + fuel_saved + lounges - fee
    match = profile["lifestyle"] in card["lifestyles"]
    return {
        "rewards_year": round(rewards), "fuel_saved": round(fuel_saved),
        "lounge_value": round(lounges), "annual_fee_paid": fee,
        "net_value": round(net), "lifestyle_match": match,
        "score": round(net + (LIFESTYLE_BONUS if match else 0)),
        "breakdown": breakdown,
    }


def recommend(profile, cards, top_n=3):
    """Rank non-FD cards for a profile. Returns (matches, filtered_out)."""
    matches, filtered = [], []
    for card in cards:
        if card["is_fd_backed"]:
            continue
        if card["joining_fee"] > profile["max_joining_fee"]:
            filtered.append({"id": card["id"], "reason": "Joining fee above your limit"})
        elif profile["salary"] < card["min_income"]:
            filtered.append({"id": card["id"], "reason": "Below minimum income"})
        else:
            matches.append({"card": card, **evaluate_card(card, profile)})
    matches.sort(key=lambda m: (m["score"], m["net_value"]), reverse=True)
    for rank, m in enumerate(matches, start=1):
        m["rank"] = rank
    return matches[:top_n], filtered


# -------------------------------------------------------------- calculators
def headline_rate(card, category):
    rule = card["rates"].get(category)
    return rule["rate"] if rule else card["base_rate"]


def cashback(card, category, monthly_spend, monthly_cap=0):
    rate = headline_rate(card, category)
    per_month = monthly_spend * rate
    if monthly_cap and monthly_cap > 0:
        per_month = min(per_month, monthly_cap)
    rule = card["rates"].get(category) or {}
    return {"rate_pct": round(rate * 100, 2), "per_month": round(per_month, 2),
            "per_year": round(per_month * MONTHS, 2), "card_cap": rule.get("cap")}


def interest(balance, annual_rate_pct, months, monthly_payment):
    """Simulate paying down a revolving credit-card balance month by month."""
    errors = {}
    balance = _to_number(balance, "balance", errors, required=True, minimum=1)
    rate = _to_number(annual_rate_pct, "annual_rate", errors, required=True, minimum=0, maximum=100)
    months = _to_number(months, "months", errors, required=True, minimum=1, maximum=600)
    payment = _to_number(monthly_payment, "monthly_payment", errors, required=True, minimum=0)
    if errors:
        raise ValidationError(errors)
    months = int(months)
    monthly_rate = rate / 12 / 100
    owed, total_interest, total_paid, schedule = balance, 0.0, 0.0, []
    for m in range(1, months + 1):
        if owed <= 0.005:
            break
        charge = owed * monthly_rate
        owed += charge
        paid = min(payment, owed)
        owed -= paid
        total_interest += charge
        total_paid += paid
        schedule.append({"month": m, "interest": round(charge, 2), "paid": round(paid, 2),
                         "balance": round(max(owed, 0), 2)})
    first_interest = balance * monthly_rate
    return {
        "monthly_rate_pct": round(monthly_rate * 100, 2),
        "interest_paid": round(total_interest), "total_paid": round(total_paid),
        "still_owed": round(max(owed, 0)), "cleared": owed <= 0.5,
        "never_reduces": payment <= first_interest and monthly_rate > 0,
        "schedule": schedule,
    }


def fd_options(cards, amount):
    """FD-backed cards with eligibility and the credit limit the FD would give."""
    out = []
    for card in cards:
        if not card["is_fd_backed"]:
            continue
        eligible = amount >= card["fd_min"]
        out.append({"card": card, "eligible": eligible,
                    "credit_limit": round(amount * card["fd_limit_pct"]) if eligible else 0,
                    "shortfall": 0 if eligible else round(card["fd_min"] - amount)})
    out.sort(key=lambda o: (not o["eligible"], -o["credit_limit"]))
    return out
