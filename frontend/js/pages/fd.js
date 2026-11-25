/** FD-backed cards: enter a deposit, see which cards it unlocks. */
import { api } from "../api.js";
import { fdTile } from "../cardview.js";
import { $, debounce } from "../util.js";

export async function mount(root) {
  root.innerHTML = `<h1>FD-backed cards</h1>
    <p class="lede">No salary slip or credit history? Open a fixed deposit and get a card with a limit of 75–100% of it. Your FD keeps earning interest.</p>
    <div style="max-width:320px"><label for="amount">Your FD amount (₹)</label><input id="amount" type="number" min="0" step="1000" value="50000"><p class="field-error" id="amount-err" role="alert"></p></div>
    <div class="cards-grid" id="grid" aria-live="polite"></div>`;
  async function load() {
    const err = $("#amount-err", root);
    err.textContent = "";
    try {
      const { options } = await api.fdCards($("#amount", root).value || 0);
      $("#grid", root).innerHTML = options.map(fdTile).join("");
    } catch (e) { err.textContent = e.message; }
  }
  $("#amount", root).addEventListener("input", debounce(load, 250));
  await load();
}
