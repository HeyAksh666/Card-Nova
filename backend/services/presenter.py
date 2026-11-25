"""Turns raw card rows into display-ready dictionaries (formatting only)."""


def inr(value):
    """Indian digit grouping: 1234567 -> '12,34,567'."""
    n = int(round(value))
    sign, s = ("-" if n < 0 else ""), str(abs(n))
    if len(s) <= 3:
        return f"{sign}₹{s}"
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return f"{sign}₹{','.join(parts)},{tail}"


def compact(value):
    if value >= 100000:
        return f"₹{value / 100000:g}L"
    if value >= 1000:
        return f"₹{value / 1000:g}K"
    return f"₹{value}"


def fee_text(card):
    joining = "Free" if not card["joining_fee"] else inr(card["joining_fee"])
    annual = "Free" if not card["annual_fee"] else inr(card["annual_fee"])
    text = f"Joining {joining} · Annual {annual}"
    if card["fee_waiver_spend"] and card["annual_fee"]:
        text += f" (Waived on {compact(card['fee_waiver_spend'])} annual spend)"
    elif card["fee_note"]:
        text += f" ({card['fee_note']})"
    return text


def lounge_text(card):
    d, i = card["lounge_domestic"], card["lounge_international"]
    if d and i:
        return f"Up to {d} domestic + {i} international"
    if d:
        return f"{d} domestic/year"
    if i:
        return f"{i} international/year"
    return "None"


def present_card(card):
    out = dict(card)
    out["display"] = {
        "fee": fee_text(card),
        "fuel": card["fuel"]["label"] if card.get("fuel") else "None",
        "lounge": lounge_text(card),
        "fd_min": inr(card["fd_min"]) if card.get("fd_min") else None,
    }
    return out
