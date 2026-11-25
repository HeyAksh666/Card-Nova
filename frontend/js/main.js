/** Hash router + navigation state. */
import { session } from "./api.js";
import { $, $$, esc } from "./util.js";

const ROUTES = {
  matches: { title: "My card matches", load: () => import("./pages/matches.js") },
  cards: { title: "All credit cards", load: () => import("./pages/cards.js") },
  calculators: { title: "Cashback & interest calculators", load: () => import("./pages/calculators.js") },
  "fd-cards": { title: "FD-backed credit cards", load: () => import("./pages/fd.js") },
  account: { title: "Your account", load: () => import("./pages/account.js") },
};
const app = $("#app");

function refreshAccountLink() {
  const link = $("#account-link"), user = session.user;
  link.textContent = session.token && user ? user.name.split(" ")[0] : "Sign in (optional)";
}

async function render() {
  const name = (location.hash.replace(/^#\/?/, "") || "matches").split("?")[0];
  const route = ROUTES[name] || ROUTES.matches;
  const key = ROUTES[name] ? name : "matches";
  $$("[data-route]").forEach((a) => (a.dataset.route === key ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
  document.title = `${route.title} — Card Nova`;
  app.innerHTML = `<p class="hint" role="status">Loading…</p>`;
  try {
    const page = await route.load();
    app.innerHTML = "";
    await page.mount(app, { onAuthChange: refreshAccountLink });
  } catch (err) {
    app.innerHTML = `<div class="notice" role="alert">${esc(err.message || "Something went wrong.")} <a href="#/matches">Back to my matches</a></div>`;
  }
  app.focus({ preventScroll: true });
}

window.addEventListener("hashchange", () => { window.scrollTo(0, 0); render(); });
refreshAccountLink();
render();
