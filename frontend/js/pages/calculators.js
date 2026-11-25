/** Cashback and interest calculators (all maths is done by the API). */
import { api } from "../api.js";
import { $, debounce, esc, inr } from "../util.js";

export async function mount(root) {
  const [meta, { cards }] = await Promise.all([api.meta(), api.cards({ fd: 0 })]);
  root.innerHTML = `<div class="calc-grid">
    <section class="panel" aria-labelledby="cb-h"><h2 id="cb-h">Cashback calculator</h2>
      <div><label for="cb-card">Card</label><select id="cb-card">${cards.map((c) => `<option value="${esc(c.id)}">${esc(c.bank)} ${esc(c.name)}</option>`).join("")}</select></div>
      <div><label for="cb-cat">Spend category</label><select id="cb-cat">${Object.entries(meta.categories).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("")}</select></div>
      <div><label for="cb-spend">Monthly spend (₹)</label><input id="cb-spend" type="number" min="0" value="10000"></div>
      <div><label for="cb-cap">Monthly cashback cap (₹, 0 = none)</label><input id="cb-cap" type="number" min="0" value="0"><p class="hint" id="cb-hint"></p></div>
      <p class="warn" id="cb-err" role="alert"></p>
      <div class="readout" aria-live="polite"><div><small>Rate</small><b id="cb-rate">–</b></div><div><small>Per month</small><b id="cb-month">–</b></div><div><small>Per year</small><b class="gold" id="cb-year">–</b></div></div>
    </section>
    <section class="panel" aria-labelledby="in-h"><h2 id="in-h">Interest calculator</h2><p class="sub">See what carrying an unpaid balance costs you.</p>
      <div class="grid-2"><div><label for="in-bal">Outstanding balance (₹)</label><input id="in-bal" type="number" min="0" value="50000"></div>
        <div><label for="in-rate">Annual interest rate (%)</label><input id="in-rate" type="number" min="0" max="100" step="0.1" value="42"></div>
        <div><label for="in-months">Months</label><input id="in-months" type="number" min="1" max="600" value="12"></div>
        <div><label for="in-pay">Monthly payment (₹)</label><input id="in-pay" type="number" min="0" value="5000"></div></div>
      <p class="warn" id="in-err" role="alert"></p>
      <div class="readout" aria-live="polite"><div><small>Monthly rate</small><b id="in-mrate">–</b></div><div><small>Interest paid</small><b class="gold" id="in-int">–</b></div><div><small>Still owed</small><b id="in-owed">–</b></div></div>
      <details class="sched"><summary>Month-by-month schedule</summary><div class="schedule" id="in-sched"></div></details>
    </section></div>`;

  async function cashback() {
    const err = $("#cb-err", root); err.textContent = "";
    try {
      const r = await api.cashback({ card_id: $("#cb-card", root).value, category: $("#cb-cat", root).value,
        monthly_spend: $("#cb-spend", root).value, monthly_cap: $("#cb-cap", root).value || 0 });
      $("#cb-rate", root).textContent = r.rate_pct + "%";
      $("#cb-month", root).textContent = inr(r.per_month);
      $("#cb-year", root).textContent = inr(r.per_year);
      $("#cb-hint", root).textContent = r.card_cap ? `This card's own cap on this category is ${inr(r.card_cap)} a month.` : "";
    } catch (e) { err.textContent = e.status === 400 ? "Enter a monthly spend of 0 or more." : e.message; }
  }

  async function interest() {
    const err = $("#in-err", root); err.textContent = "";
    try {
      const r = await api.interest({ balance: $("#in-bal", root).value, annual_rate: $("#in-rate", root).value,
        months: $("#in-months", root).value, monthly_payment: $("#in-pay", root).value });
      $("#in-mrate", root).textContent = r.monthly_rate_pct.toFixed(2) + "%";
      $("#in-int", root).textContent = inr(r.interest_paid);
      $("#in-owed", root).textContent = inr(r.still_owed);
      if (r.never_reduces) err.textContent = "Your payment is no more than the monthly interest, so the balance will never go down.";
      else if (r.cleared) err.textContent = `Balance cleared in ${r.schedule.length} month${r.schedule.length === 1 ? "" : "s"}.`;
      $("#in-sched", root).innerHTML = `<table><thead><tr><th>Month</th><th>Interest</th><th>Paid</th><th>Balance</th></tr></thead><tbody>${
        r.schedule.map((s) => `<tr><td>${s.month}</td><td>${inr(s.interest)}</td><td>${inr(s.paid)}</td><td>${inr(s.balance)}</td></tr>`).join("")}</tbody></table>`;
    } catch (e) { err.textContent = e.status === 400 ? "Check the numbers: balance, rate, months and payment must be valid." : e.message; }
  }

  const cbLater = debounce(cashback, 200), inLater = debounce(interest, 200);
  ["cb-card", "cb-cat", "cb-spend", "cb-cap"].forEach((id) => $("#" + id, root).addEventListener("input", cbLater));
  ["in-bal", "in-rate", "in-months", "in-pay"].forEach((id) => $("#" + id, root).addEventListener("input", inLater));
  await Promise.all([cashback(), interest()]);
}
