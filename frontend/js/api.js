/** Thin wrapper around the Card Nova REST API. */
const TOKEN_KEY = "cardnova.token";
const USER_KEY = "cardnova.user";

export const session = {
  get token() { return localStorage.getItem(TOKEN_KEY); },
  get user() { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } },
  set(token, user) { localStorage.setItem(TOKEN_KEY, token); localStorage.setItem(USER_KEY, JSON.stringify(user)); },
  clear() { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); },
};

export class ApiError extends Error {
  constructor(message, status, details) { super(message); this.status = status; this.details = details || {}; }
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (session.token) headers.Authorization = "Bearer " + session.token;
  let res;
  try {
    res = await fetch("/api" + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError("Can't reach the server. Is it running?", 0);
  }
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && session.token) session.clear(); // expired token
  if (!res.ok) throw new ApiError(data.error || "Something went wrong", res.status, data.details);
  return data;
}

const qs = (params) => {
  const p = new URLSearchParams(Object.entries(params || {}).filter(([, v]) => v !== "" && v != null));
  return p.toString() ? "?" + p : "";
};

export const api = {
  meta: () => request("/meta"),
  cards: (params) => request("/cards" + qs(params)),
  recommend: (profile) => request("/recommend", { method: "POST", body: profile }),
  fdCards: (amount) => request("/fd-cards" + qs({ amount })),
  cashback: (body) => request("/calc/cashback", { method: "POST", body }),
  interest: (body) => request("/calc/interest", { method: "POST", body }),
  register: (body) => request("/auth/register", { method: "POST", body }),
  login: (body) => request("/auth/login", { method: "POST", body }),
  me: () => request("/auth/me"),
  getProfile: () => request("/profile"),
  saveProfile: (profile) => request("/profile", { method: "PUT", body: profile }),
};
