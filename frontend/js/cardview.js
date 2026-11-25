/** Reusable card artwork and tile markup. */
import { esc, inr } from "./util.js";

export const SPARK = `<svg class="spark" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"/><path d="M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7z"/></svg>`;
const icon = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const ICONS = {
  fee: icon('<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M16 15h2"/>'),
  fuel: icon('<path d="M4 20V5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v15M3 20h12M14 9h2.5a1.5 1.5 0 0 1 1.5 1.5V16a1.5 1.5 0 0 0 3 0V8l-3-3"/>'),
  lounge: icon('<path d="M10.5 13.5L4 11l1.5-1.5 7 .5 5-5a1.8 1.8 0 0 1 2.5 2.5l-5 5 .5 7L14 21l-2.5-6.5L8 18l-2 .5.5-2z"/>'),
};

export function cardArt(card) {
  return `<div class="cc theme-${esc(card.theme)}" role="img" aria-label="${esc(card.bank)} ${esc(card.name)} card">
    <div class="cc-top"><span class="cc-logo">${SPARK}<span>CARD <em>NOVA</em></span></span><span class="cc-bank">${esc(card.bank)}</span></div>
    <span class="chip"></span>
    <div class="cc-name">${esc(card.name)}</div>
    <div class="cc-dots">•••• •••• •••• NOVA</div>
  </div>`;
}

function details(card) {
  const d = card.display;
  return `<ul class="facts">
    <li>${ICONS.fee}<span>${esc(d.fee)}</span></li>
    <li>${ICONS.fuel}<span>${esc(d.fuel)}</span></li>
    <li>${ICONS.lounge}<span>Lounge: ${esc(d.lounge)}</span></li>
  </ul>
  <ul class="perks">${card.highlights.map((h) => `<li>${esc(h)}</li>`).join("")}</ul>`;
}

const badges = (card, extra = "") => `<div class="badges"><span class="badge">${esc(card.tier)}</span>${
  card.is_fd_backed ? `<span class="badge badge-gold">FD-backed · min ${esc(card.display.fd_min)}</span>` : ""}${extra}</div>`;

const head = (card, right = "") => `<div class="tile-head"><div><div class="bank">${esc(card.bank)}</div><h3>${esc(card.name)}</h3></div>${right}</div>`;

/** Plain catalogue tile with an "Apply" link. */
export function catalogTile(card) {
  return `<article class="tile">${head(card)}${cardArt(card)}${badges(card)}${details(card)}
    <a class="btn btn-outline" href="${esc(card.apply_url)}" target="_blank" rel="noopener noreferrer">Apply on ${esc(card.bank)} website
      <svg class="spark" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg></a></article>`;
}

/** Ranked recommendation tile with rewards/fuel/net stats and a per-category breakdown. */
export function matchTile(m, categories) {
  const c = m.card;
  const rows = Object.entries(m.breakdown).map(([k, v]) => `<tr><td>${esc(categories[k] || k)}</td><td>${inr(v)}</td></tr>`).join("");
  const extras = [];
  if (m.lounge_value) extras.push(`<tr><td>Lounge access (estimated)</td><td>${inr(m.lounge_value)}</td></tr>`);
  extras.push(`<tr><td>Annual fee paid</td><td>−${inr(m.annual_fee_paid)}</td></tr>`);
  return `<article class="tile">${head(c, `<span class="rank" aria-label="Rank ${m.rank}">#${m.rank}</span>`)}${cardArt(c)}
    ${badges(c, m.lifestyle_match ? `<span class="badge badge-match">Fits your lifestyle</span>` : "")}${details(c)}
    <div class="stats"><div><small>Rewards/yr</small><b>${inr(m.rewards_year)}</b></div>
      <div><small>Fuel saved</small><b>${inr(m.fuel_saved)}</b></div>
      <div><small>Net value</small><b class="gold">${inr(m.net_value)}</b></div></div>
    <details><summary>How this is worked out</summary><table>${rows}${extras.join("")}</table></details>
    <a class="btn btn-outline" href="${esc(c.apply_url)}" target="_blank" rel="noopener noreferrer">Apply on ${esc(c.bank)} website</a></article>`;
}

/** FD-backed tile: shows the limit the person's deposit would unlock. */
export function fdTile(o) {
  const c = o.card;
  const foot = o.eligible
    ? `<div class="limit"><span>Your credit limit</span><b>${inr(o.credit_limit)}</b></div>`
    : `<div class="limit"><span>Add ${inr(o.shortfall)} to your FD to qualify</span></div>`;
  return `<article class="tile ${o.eligible ? "" : "dim"}">${head(c)}${cardArt(c)}${badges(c)}${details(c)}${foot}
    <a class="btn btn-outline" href="${esc(c.apply_url)}" target="_blank" rel="noopener noreferrer">Apply on ${esc(c.bank)} website</a></article>`;
}
