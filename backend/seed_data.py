"""Seed catalogue of credit cards.

NOTE: figures are representative and meant for a student/demo project. Real
bank offers change often - always confirm on the bank's website before applying.
Rate rule: {"rate": headline reward rate, "cap": monthly reward cap in Rs (None = no cap),
            "share": fraction of the category spend that is eligible (default 1.0)}
"""

BANK_URLS = {
    "SBI Card": "https://www.sbicard.com",
    "ICICI Bank": "https://www.icicibank.com",
    "Axis Bank": "https://www.axisbank.com",
    "HDFC Bank": "https://www.hdfcbank.com",
    "Kotak Mahindra Bank": "https://www.kotak.com",
    "IDFC FIRST Bank": "https://www.idfcfirstbank.com",
}
BANK_THEMES = {
    "SBI Card": "navy", "ICICI Bank": "emerald", "Axis Bank": "maroon",
    "HDFC Bank": "indigo", "Kotak Mahindra Bank": "umber", "IDFC FIRST Bank": "slate",
}


def _card(cid, bank, name, tier, joining, annual, waiver=None, note=None, base=0.01,
          rates=None, fuel=None, lounge=(0, 0), lifestyles=(), highlights=(),
          min_income=20000, fd_min=None, fd_pct=None):
    return {
        "id": cid, "bank": bank, "name": name, "tier": tier,
        "joining_fee": joining, "annual_fee": annual, "fee_waiver_spend": waiver,
        "fee_note": note, "base_rate": base, "rates": rates or {}, "fuel": fuel,
        "lounge_domestic": lounge[0], "lounge_international": lounge[1],
        "lifestyles": list(lifestyles), "highlights": list(highlights),
        "min_income": min_income, "is_fd_backed": 1 if fd_min else 0,
        "fd_min": fd_min, "fd_limit_pct": fd_pct,
        "apply_url": BANK_URLS[bank], "theme": BANK_THEMES[bank],
    }


def _fuel(label, cap=100, pct=0.01):
    return {"pct": pct, "monthly_cap": cap, "label": label}


CARDS = [
    _card("sbi-cashback", "SBI Card", "Cashback Card", "Mid", 999, 999, 200000,
          base=0.01, rates={"online_shopping": {"rate": 0.05, "cap": 5000},
                            "fuel": {"rate": 0}, "utilities": {"rate": 0}},
          fuel=_fuel("1% on ₹500–₹3,000"), lifestyles=["online_shopper", "everyday_saver"],
          highlights=["5% cashback on all online spends", "1% offline"], min_income=25000),
    _card("sbi-bpcl-octane", "SBI Card", "BPCL Octane", "Mid", 1499, 1499, 200000,
          base=0.0025, rates={"dining": {"rate": 0.025}, "groceries": {"rate": 0.025, "cap": 1000},
                              "fuel": {"rate": 0.0725, "cap": 150}},
          fuel=_fuel("1% at BPCL up to ₹4,000"), lounge=(4, 0),
          lifestyles=["daily_commuter", "foodie"],
          highlights=["7.25% value back on BPCL fuel", "10X on dining, groceries, movies"],
          min_income=30000),
    _card("sbi-simplyclick", "SBI Card", "SimplyCLICK", "Entry", 499, 499, 100000,
          base=0.0025, rates={"online_shopping": {"rate": 0.025, "cap": 1000},
                              "fuel": {"rate": 0}, "utilities": {"rate": 0}},
          fuel=_fuel("1% on ₹500–₹3,000"), lifestyles=["online_shopper"],
          highlights=["10X points with online partners", "₹500 Amazon voucher on joining"]),
    _card("icici-amazon-pay", "ICICI Bank", "Amazon Pay", "Entry", 0, 0, note="Lifetime free",
          base=0.01, rates={"online_shopping": {"rate": 0.05, "share": 0.7},
                            "dining": {"rate": 0.02, "share": 0.5},
                            "travel": {"rate": 0.02, "share": 0.5},
                            "utilities": {"rate": 0.02, "share": 0.5}, "fuel": {"rate": 0}},
          fuel=_fuel("1% at all fuel stations"), lifestyles=["online_shopper", "everyday_saver"],
          highlights=["5% back on Amazon for Prime members", "2% on Amazon Pay partners"]),
    _card("icici-coral", "ICICI Bank", "Coral", "Entry", 500, 500, 150000,
          base=0.005, rates={"dining": {"rate": 0.01}, "fuel": {"rate": 0}, "utilities": {"rate": 0}},
          fuel=_fuel("1% on ₹400–₹4,000"), lounge=(4, 0), lifestyles=["everyday_saver", "foodie"],
          highlights=["2 reward points per ₹100", "Movie and dining offers"], min_income=25000),
    _card("icici-emeralde-private", "ICICI Bank", "Emeralde Private Metal", "Premium", 12499, 12499,
          1500000, base=0.015, rates={"travel": {"rate": 0.03}, "dining": {"rate": 0.02},
                                      "fuel": {"rate": 0}},
          fuel=_fuel("1% up to ₹4,000", cap=400), lounge=(16, 8),
          lifestyles=["frequent_traveller", "foodie"],
          highlights=["16 domestic + 8 international lounge visits", "Metal card with concierge"],
          min_income=100000),
    _card("axis-ace", "Axis Bank", "ACE", "Entry", 499, 499, 200000, base=0.015,
          rates={"utilities": {"rate": 0.05, "cap": 500, "share": 0.5},
                 "dining": {"rate": 0.04, "cap": 500, "share": 0.6}, "fuel": {"rate": 0}},
          fuel=_fuel("1% on ₹400–₹4,000"), lifestyles=["everyday_saver", "foodie"],
          highlights=["5% on bill payments via Google Pay", "4% on Swiggy, Zomato, Ola"]),
    _card("axis-atlas", "Axis Bank", "Atlas", "Premium", 5000, 5000, None, note="Milestone EDGE Miles",
          base=0.01, rates={"travel": {"rate": 0.025}, "fuel": {"rate": 0}}, fuel=None,
          lounge=(18, 12), lifestyles=["frequent_traveller"],
          highlights=["5 EDGE Miles per ₹100 on travel", "Tiered milestone miles"], min_income=50000),
    _card("axis-indianoil", "Axis Bank", "IndianOil", "Entry", 500, 500, 50000, base=0.005,
          rates={"fuel": {"rate": 0.04, "cap": 100}},
          fuel=_fuel("1% at all stations up to ₹4,000"), lifestyles=["daily_commuter"],
          highlights=["4% value back at IndianOil", "Movie discounts"]),
    _card("hdfc-millennia", "HDFC Bank", "Millennia", "Mid", 1000, 1000, 100000, base=0.01,
          rates={"online_shopping": {"rate": 0.05, "cap": 1000}, "fuel": {"rate": 0},
                 "utilities": {"rate": 0}},
          fuel=_fuel("1% on ₹400–₹5,000", cap=250), lounge=(8, 0),
          lifestyles=["online_shopper", "everyday_saver"],
          highlights=["5% cashback on Amazon, Flipkart, Myntra and more", "8 domestic lounge visits a year"],
          min_income=35000),
    # ---- FD-backed cards (no income proof / credit history needed) ----
    _card("kotak-811-fd", "Kotak Mahindra Bank", "811 Dream Different (FD-backed)", "Entry", 0, 0,
          note="Lifetime free", base=0.0025, fuel=_fuel("1% on ₹500–₹3,000"),
          lifestyles=["everyday_saver"], min_income=0, fd_min=10000, fd_pct=0.9,
          highlights=["Limit up to 90% of FD", "Builds credit score", "No income proof needed"]),
    _card("sbi-unnati-fd", "SBI Card", "Unnati (FD-backed)", "Entry", 0, 499, note="Free for 4 years",
          base=0.0025, fuel=_fuel("1% on ₹500–₹3,000"), lifestyles=["everyday_saver"], min_income=0,
          fd_min=25000, fd_pct=0.8,
          highlights=["Against SBI FD of ₹25,000+", "Credit history for new-to-credit"]),
    _card("icici-instant-platinum-fd", "ICICI Bank", "Instant Platinum (FD-backed)", "Entry", 0, 0,
          note="Lifetime free", base=0.0025, fuel=_fuel("1% at HPCL"), lifestyles=["everyday_saver"],
          min_income=0, fd_min=20000, fd_pct=0.8,
          highlights=["Limit up to 80% of FD", "FD keeps earning interest"]),
    _card("axis-insta-easy-fd", "Axis Bank", "Insta Easy (FD-backed)", "Entry", 0, 0,
          note="Lifetime free", base=0.0025, fuel=_fuel("1% on ₹400–₹4,000"),
          lifestyles=["everyday_saver"], min_income=0, fd_min=20000, fd_pct=0.8,
          highlights=["Limit up to 80% of FD", "Instant digital issuance"]),
    _card("idfc-wow-fd", "IDFC FIRST Bank", "WOW! (FD-backed)", "Entry", 0, 0, note="Lifetime free",
          base=0.0025, fuel=_fuel("1% at all fuel stations"), lifestyles=["everyday_saver"],
          min_income=0, fd_min=20000, fd_pct=1.0,
          highlights=["Limit up to 100% of FD", "FD keeps earning interest"]),
]
