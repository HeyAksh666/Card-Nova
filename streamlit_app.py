"""Card Nova - Streamlit edition.

Same recommendation engine and card catalogue as the Flask version
(backend/services/engine.py, backend/seed_data.py), with a Streamlit interface
so it can be hosted free on Streamlit Community Cloud.

Run locally:  streamlit run streamlit_app.py
"""
import streamlit as st

from backend.seed_data import CARDS
from backend.services import engine
from backend.services.presenter import inr, present_card

st.set_page_config(page_title="Card Nova", page_icon="✨", layout="wide")

THEMES = {
    "navy": "#0c2145,#050d1d", "emerald": "#0c3024,#04120d", "maroon": "#451020,#170509",
    "umber": "#33201a,#0f0906", "indigo": "#1b2152,#080a1c", "slate": "#263042,#0a0d13",
}
st.markdown("""
<style>
.cc{position:relative;aspect-ratio:1.586;border-radius:12px;padding:14px 16px;overflow:hidden;
    border:1px solid rgba(255,255,255,.08);margin:6px 0 10px}
.cc .top{display:flex;justify-content:space-between;font-size:.72rem;letter-spacing:.1em;color:rgba(255,255,255,.65)}
.cc .logo{font-weight:700;color:#f4f0e6}.cc .logo b{color:#cba965}
.cc .chip{position:absolute;left:16px;bottom:16px;width:14%;aspect-ratio:1.3;border-radius:4px;
    background:linear-gradient(135deg,#e5cd94,#a98a4e 60%,#cdb078)}
.cc .nm{position:absolute;right:16px;bottom:34px;font-size:1.25rem;font-weight:600;text-align:right;max-width:70%}
.cc .dots{position:absolute;right:16px;bottom:14px;font-size:.6rem;letter-spacing:.18em;color:rgba(255,255,255,.5)}
.bank{color:#cba965;font-size:.72rem;letter-spacing:.2em;text-transform:uppercase}
.facts{color:#c4bfb3;font-size:.9rem;line-height:1.7}
</style>""", unsafe_allow_html=True)


def card_art(card):
    a, b = THEMES.get(card["theme"], THEMES["slate"]).split(",")
    return (f'<div class="cc" style="background:linear-gradient(135deg,{a},{b} 70%)">'
            f'<div class="top"><span class="logo">✦ CARD <b>NOVA</b></span><span>{card["bank"].upper()}</span></div>'
            f'<span class="chip"></span><div class="nm">{card["name"]}</div>'
            f'<div class="dots">•••• •••• •••• NOVA</div></div>')


def card_body(card):
    c = present_card(card)
    d = c["display"]
    st.markdown(f'<div class="bank">{c["bank"]}</div>', unsafe_allow_html=True)
    st.subheader(c["name"])
    st.markdown(card_art(c), unsafe_allow_html=True)
    badge = f"`{c['tier']}`" + (f" `FD-backed · min {d['fd_min']}`" if c["is_fd_backed"] else "")
    st.markdown(badge)
    st.markdown(f'<div class="facts">💳 {d["fee"]}<br>⛽ {d["fuel"]}<br>✈️ Lounge: {d["lounge"]}</div>',
                unsafe_allow_html=True)
    st.markdown("\n".join(f"- {h}" for h in c["highlights"]))


def apply_button(card, key):
    st.link_button(f"Apply on {card['bank']} website", card["apply_url"], width="stretch")


def grid(cards, render, per_row=3):
    for i in range(0, len(cards), per_row):
        cols = st.columns(per_row)
        for col, item in zip(cols, cards[i:i + per_row]):
            with col, st.container(border=True):
                render(item)


# ------------------------------------------------------------------ pages
def page_matches():
    st.title("Your money profile")
    saved = st.session_state.get("profile", {
        "name": "", "salary": 60000, "lifestyle": "everyday_saver", "max_joining_fee": 1000,
        "expenses": {"online_shopping": 8000, "dining": 4000, "travel": 3000,
                     "fuel": 3000, "groceries": 6000, "utilities": 4000}})
    with st.form("profile"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name on card", saved["name"], max_chars=26)
        salary = c2.number_input("Monthly salary (₹)", 0, 10_000_000, int(saved["salary"]), step=1000)
        keys = list(engine.LIFESTYLES)
        lifestyle = c1.selectbox("Lifestyle", keys, keys.index(saved["lifestyle"]),
                                 format_func=engine.LIFESTYLES.get)
        max_fee = c2.number_input("Max joining fee I'll pay (₹)", 0, 1_000_000, int(saved["max_joining_fee"]), step=500)
        st.subheader("Monthly expenses (₹)")
        cols = st.columns(3)
        expenses = {k: cols[i % 3].number_input(label, 0, 10_000_000, int(saved["expenses"][k]), step=500)
                    for i, (k, label) in enumerate(engine.CATEGORIES.items())}
        submitted = st.form_submit_button("Save profile", type="primary")
    if submitted:
        st.session_state["profile"] = {"name": name, "salary": salary, "lifestyle": lifestyle,
                                       "max_joining_fee": max_fee, "expenses": expenses}
    profile_raw = st.session_state.get("profile", saved)
    try:
        profile = engine.validate_profile(profile_raw)
    except engine.ValidationError as exc:
        st.error("Check these fields: " + ", ".join(exc.errors))
        return
    holder = profile["name"] or "Your name"
    st.caption(f"Card holder: **{holder.upper()}**")
    matches, filtered = engine.recommend(profile, CARDS)
    st.header("Best cards for you")
    st.caption("Ranked by yearly rewards + fuel savings − fees, matched to your lifestyle.")
    if not matches:
        st.info("No cards fit these limits. Raise your maximum joining fee, or try the FD-backed cards tab.")
        return
    if filtered:
        st.caption(f"{len(filtered)} card(s) left out: joining fee above your limit or income below the bank's minimum.")
    cols = st.columns(3)
    for col, m in zip(cols, matches):
        with col, st.container(border=True):
            st.markdown(f"### #{m['rank']}")
            card_body(m["card"])
            if m["lifestyle_match"]:
                st.success("Fits your lifestyle")
            a, b, c = st.columns(3)
            a.metric("Rewards/yr", inr(m["rewards_year"]))
            b.metric("Fuel saved", inr(m["fuel_saved"]))
            c.metric("Net value", inr(m["net_value"]))
            with st.expander("How this is worked out"):
                rows = {engine.CATEGORIES[k]: inr(v) for k, v in m["breakdown"].items()}
                if m["lounge_value"]:
                    rows["Lounge access (estimated)"] = inr(m["lounge_value"])
                rows["Annual fee paid"] = "−" + inr(m["annual_fee_paid"])
                st.table(rows)
            apply_button(m["card"], f"m{m['rank']}")


def page_cards():
    st.title("All credit cards")
    c1, c2, c3 = st.columns([2, 1, 1])
    q = c1.text_input("Search", placeholder="Card or bank name").strip().lower()
    banks = sorted({c["bank"] for c in CARDS})
    tiers = sorted({c["tier"] for c in CARDS})
    bank = c2.selectbox("Bank", ["All banks"] + banks)
    tier = c3.selectbox("Tier", ["All tiers"] + tiers)
    cards = [c for c in CARDS
             if (not q or q in c["name"].lower() or q in c["bank"].lower())
             and (bank == "All banks" or c["bank"] == bank) and (tier == "All tiers" or c["tier"] == tier)]
    st.caption(f"{len(cards)} card{'s' if len(cards) != 1 else ''}")
    if not cards:
        st.info("No cards match these filters. Clear the search or pick another bank.")
    grid(cards, lambda c: (card_body(c), apply_button(c, c["id"])))


def page_calculators():
    st.title("Calculators")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Cashback calculator")
        regular = [c for c in CARDS if not c["is_fd_backed"]]
        card = st.selectbox("Card", regular, format_func=lambda c: f"{c['bank']} {c['name']}")
        cat = st.selectbox("Spend category", list(engine.CATEGORIES), format_func=engine.CATEGORIES.get)
        spend = st.number_input("Monthly spend (₹)", 0, 10_000_000, 10000, step=500)
        cap = st.number_input("Monthly cashback cap (₹, 0 = none)", 0, 10_000_000, 0, step=100)
        r = engine.cashback(card, cat, spend, cap)
        a, b, c = st.columns(3)
        a.metric("Rate", f"{r['rate_pct']:g}%")
        b.metric("Per month", inr(r["per_month"]))
        c.metric("Per year", inr(r["per_year"]))
        if r["card_cap"]:
            st.caption(f"This card's own cap on this category is {inr(r['card_cap'])} a month.")
    with right, st.container(border=True):
        st.subheader("Interest calculator")
        st.caption("See what carrying an unpaid balance costs you.")
        c1, c2 = st.columns(2)
        bal = c1.number_input("Outstanding balance (₹)", 0, 10_000_000, 50000, step=1000)
        rate = c2.number_input("Annual interest rate (%)", 0.0, 100.0, 42.0, step=0.5)
        months = c1.number_input("Months", 0, 600, 12)
        pay = c2.number_input("Monthly payment (₹)", 0, 10_000_000, 5000, step=500)
        try:
            r = engine.interest(bal, rate, months, pay)
        except engine.ValidationError:
            st.warning("Enter a balance of at least ₹1 and at least 1 month.")
            return
        a, b, c = st.columns(3)
        a.metric("Monthly rate", f"{r['monthly_rate_pct']:.2f}%")
        b.metric("Interest paid", inr(r["interest_paid"]))
        c.metric("Still owed", inr(r["still_owed"]))
        if r["never_reduces"]:
            st.error("Your payment is no more than the monthly interest, so the balance will never go down.")
        elif r["cleared"]:
            st.success(f"Balance cleared in {len(r['schedule'])} month(s).")
        with st.expander("Month-by-month schedule"):
            st.dataframe(r["schedule"], hide_index=True, width="stretch")


def page_fd():
    st.title("FD-backed cards")
    st.write("No salary slip or credit history? Open a fixed deposit and get a card with a limit of "
             "75–100% of it. Your FD keeps earning interest.")
    amount = st.number_input("Your FD amount (₹)", 0, 10_000_000, 50000, step=5000)
    options = engine.fd_options(CARDS, amount)

    def render(o):
        card_body(o["card"])
        if o["eligible"]:
            st.metric("Your credit limit", inr(o["credit_limit"]))
        else:
            st.warning(f"Add {inr(o['shortfall'])} to your FD to qualify")
        apply_button(o["card"], o["card"]["id"])
    grid(options, render)


PAGES = {"My matches": page_matches, "All cards": page_cards,
         "Calculators": page_calculators, "FD-backed cards": page_fd}
with st.sidebar:
    st.markdown("## ✦ CARD **NOVA**")
    choice = st.radio("Go to", list(PAGES), label_visibility="collapsed")
    st.caption("College software-engineering project. Card details are representative; confirm fees and "
               "rewards on the bank's website before applying.")
PAGES[choice]()
