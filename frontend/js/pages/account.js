/** Optional account: register, sign in, sign out. Signing in syncs the saved profile. */
import { api, session } from "../api.js";
import { $, esc } from "../util.js";

function field(id, label, type, extra = "") {
  return `<div><label for="${id}">${label}</label><input id="${id}" type="${type}" ${extra}><p class="field-error" id="${id}-err" role="alert"></p></div>`;
}

export async function mount(root, { onAuthChange }) {
  const user = session.user;
  if (session.token && user) {
    root.innerHTML = `<div class="panel narrow stack"><h1>Hi, ${esc(user.name.split(" ")[0])}</h1>
      <p class="lede" style="margin:0">You're signed in as ${esc(user.email)}. Your money profile is saved to your account and loads on any device.</p>
      <a class="btn btn-primary" style="text-align:center" href="#/matches">Go to my matches</a>
      <button class="btn btn-outline" id="out" type="button">Sign out</button></div>`;
    $("#out", root).addEventListener("click", () => { session.clear(); onAuthChange(); location.hash = "#/matches"; });
    return;
  }
  let mode = "login";
  const draw = () => {
    root.innerHTML = `<div class="panel narrow"><h1>${mode === "login" ? "Sign in" : "Create account"}</h1>
      <p class="lede">An account is optional. It only saves your money profile so you can pick it up on another device.</p>
      <div class="tabs" role="tablist"><button role="tab" id="t-login" aria-selected="${mode === "login"}">Sign in</button><button role="tab" id="t-register" aria-selected="${mode === "register"}">Create account</button></div>
      <form class="stack" id="form" novalidate>
        ${mode === "register" ? field("name", "Name", "text", 'autocomplete="name"') : ""}
        ${field("email", "Email", "email", 'autocomplete="email"')}
        ${field("password", "Password", "password", `autocomplete="${mode === "login" ? "current-password" : "new-password"}" ${mode === "register" ? 'minlength="8"' : ""}`)}
        ${mode === "register" ? '<p class="hint">Use at least 8 characters.</p>' : ""}
        <p class="field-error" id="form-err" role="alert"></p>
        <button class="btn btn-primary" type="submit">${mode === "login" ? "Sign in" : "Create account"}</button></form></div>`;
    $("#t-login", root).onclick = () => { mode = "login"; draw(); };
    $("#t-register", root).onclick = () => { mode = "register"; draw(); };
    $("#form", root).addEventListener("submit", async (ev) => {
      ev.preventDefault();
      root.querySelectorAll(".field-error").forEach((n) => { n.textContent = ""; });
      const body = { email: $("#email", root).value, password: $("#password", root).value };
      if (mode === "register") body.name = $("#name", root).value;
      try {
        const res = mode === "login" ? await api.login(body) : await api.register(body);
        session.set(res.token, res.user); onAuthChange(); location.hash = "#/matches";
      } catch (err) {
        Object.entries(err.details || {}).forEach(([k, msg]) => { const n = $(`#${k}-err`, root); if (n) n.textContent = msg; });
        if (!Object.keys(err.details || {}).length) $("#form-err", root).textContent = err.message;
      }
    });
  };
  draw();
}
