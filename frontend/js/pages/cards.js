/** "All cards": searchable, filterable catalogue. */
import { api } from "../api.js";
import { catalogTile } from "../cardview.js";
import { $, debounce, esc } from "../util.js";

export async function mount(root) {
  const meta = await api.meta();
  root.innerHTML = `<h1>All credit cards</h1>
    <p class="lede">Every card we track, with fees, fuel benefits and lounge access side by side.</p>
    <div class="filters">
      <div><label for="q">Search</label><input id="q" type="search" placeholder="Card or bank name"></div>
      <div><label for="bank">Bank</label><select id="bank"><option value="">All banks</option>${meta.banks.map((b) => `<option>${esc(b)}</option>`).join("")}</select></div>
      <div><label for="tier">Tier</label><select id="tier"><option value="">All tiers</option>${meta.tiers.map((t) => `<option>${esc(t)}</option>`).join("")}</select></div>
    </div>
    <p class="hint" id="count" role="status"></p><div class="cards-grid" id="grid"></div>`;

  async function load() {
    const { cards, count } = await api.cards({ q: $("#q", root).value.trim(), bank: $("#bank", root).value, tier: $("#tier", root).value });
    $("#count", root).textContent = `${count} card${count === 1 ? "" : "s"}`;
    $("#grid", root).innerHTML = cards.length ? cards.map(catalogTile).join("")
      : `<div class="notice">No cards match these filters. Clear the search or pick another bank.</div>`;
  }
  const later = debounce(load, 250);
  $("#q", root).addEventListener("input", later);
  $("#bank", root).addEventListener("change", load);
  $("#tier", root).addEventListener("change", load);
  await load();
}
