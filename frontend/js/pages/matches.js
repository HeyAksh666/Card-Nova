/** "My matches": money profile form, live card preview, ranked recommendations. */
import { api, session } from "../api.js";
import { matchTile, SPARK } from "../cardview.js";
import { $, esc } from "../util.js";

const STORE = "cardnova.profile";
const DEFAULTS = {
  name: "", salary: 60000, lifestyle: "everyday_saver", max_joining_fee: 1000,
  expenses: { online_shopping: 8000, dining: 4000, travel: 3000, fuel: 3000, groceries: 6000, utilities: 4000 },
};

const loadLocal = () => { try { return JSON.parse(localStorage.getItem(STORE)) || null; } catch { return null; } };

function numberField(id, label, value) {
  return `<div><label for="${id}">${label}</label><input id="${id}" name="${id}" type="number" min="0" step="any" inputmode="decimal" value="${esc(value)}"><p class="field-error" id="${id}-err" role="alert"></p></div>`;
}

function readForm(root) {
  const num = (id) => $(`#${id}`, root).value;
  const profile = { name: $("#name", root).value.trim(), salary: num("salary"), lifestyle: $("#lifestyle", root).value,
    max_joining_fee: num("max_joining_fee"), expenses: {} };
  expenseIds().forEach((k) => { profile.expenses[k] = num("exp_" + k); });
  return profile;
}
const expenseIds = () => Object.keys(DEFAULTS.expenses);

function showErrors(root, details) {
  root.querySelectorAll(".field-error").forEach((e) => { e.textContent = ""; });
  root.querySelectorAll("[aria-invalid]").forEach((e) => e.removeAttribute("aria-invalid"));
  Object.entries(details || {}).forEach(([field, msg]) => {
    const id = field.startsWith("expenses.") ? "exp_" + field.slice(9) : field;
    const input = $(`#${id}`, root);
    if (input) { input.setAttribute("aria-invalid", "true"); const err = $(`#${id}-err`, root); if (err) err.textContent = msg; }
  });
}

function renderResults(root, data, meta) {
  const out = $("#results", root);
  if (!data.matches.length) {
    out.innerHTML = `<h2>Best cards for you</h2><div class="notice">No cards fit these limits. Raise your maximum joining fee, or look at <a href="#/fd-cards">FD-backed cards</a> if you have no salary slip or credit history.</div>`;
    return;
  }
  const hidden = data.filtered_out.length
    ? `<p class="hint">${data.filtered_out.length} card${data.filtered_out.length > 1 ? "s were" : " was"} left out: joining fee above your limit or income below the bank's minimum.</p>` : "";
  out.innerHTML = `<h2>Best cards for you</h2><p>Ranked by yearly rewards + fuel savings − fees, matched to your lifestyle.</p>${hidden}
    <div class="cards-grid">${data.matches.map((m) => matchTile(m, meta.categories)).join("")}</div>`;
}

export async function mount(root) {
  const meta = await api.meta();
  let profile = loadLocal() || DEFAULTS;
  if (session.token) {
    try { const remote = (await api.getProfile()).profile; if (remote) profile = remote; } catch { /* fall back to local copy */ }
  }
  const e = profile.expenses;
  root.innerHTML = `<div class="panel profile-layout">
    <form id="profile-form" novalidate>
      <h2>Your money profile</h2>
      <div class="grid-2">
        <div><label for="name">Name on card</label><input id="name" maxlength="26" autocomplete="given-name" value="${esc(profile.name)}"></div>
        ${numberField("salary", "Monthly salary (₹)", profile.salary)}
        <div><label for="lifestyle">Lifestyle</label><select id="lifestyle">${Object.entries(meta.lifestyles).map(([k, v]) =>
          `<option value="${k}" ${k === profile.lifestyle ? "selected" : ""}>${esc(v)}</option>`).join("")}</select></div>
        ${numberField("max_joining_fee", "Max joining fee I'll pay (₹)", profile.max_joining_fee)}
      </div>
      <h3>Monthly expenses (₹)</h3>
      <div class="grid-3">${Object.entries(meta.categories).map(([k, label]) => numberField("exp_" + k, esc(label), e[k] ?? 0)).join("")}</div>
      <div class="form-actions"><button class="btn btn-primary" type="submit" id="save">Save profile</button><span class="status" id="status" role="status"></span></div>
    </form>
    <div><div class="cc cc-profile" aria-hidden="true">
      <div class="cc-top"><span class="cc-logo">${SPARK}<span>CARD <em>NOVA</em></span></span><span class="cc-tier">SIGNATURE</span></div>
      <span class="chip"></span><div class="pan">5241 •••• •••• 2026</div>
      <div class="holder"><small>CARD HOLDER</small><b id="holder">${esc(profile.name || "Your name")}</b></div><span class="rupay">RuPay</span></div></div>
  </div>
  <section class="results" id="results" aria-live="polite"></section>`;

  const form = $("#profile-form", root);
  $("#name", root).addEventListener("input", (ev) => { $("#holder", root).textContent = ev.target.value.trim() || "Your name"; });

  async function run(saveIt) {
    const status = $("#status", root), btn = $("#save", root);
    status.textContent = ""; status.className = "status"; showErrors(root, null);
    btn.disabled = true;
    try {
      const body = readForm(root);
      const data = await api.recommend(body);
      renderResults(root, data, meta);
      if (saveIt) {
        localStorage.setItem(STORE, JSON.stringify(data.profile));
        if (session.token) await api.saveProfile(data.profile);
        status.textContent = session.token ? "Profile saved to your account." : "Profile saved on this device.";
      }
    } catch (err) {
      status.className = "status error";
      status.textContent = err.status === 400 ? "Fix the highlighted fields." : err.message;
      showErrors(root, err.details);
    } finally { btn.disabled = false; }
  }
  form.addEventListener("submit", (ev) => { ev.preventDefault(); run(true); });
  run(false); // show matches straight away
}
