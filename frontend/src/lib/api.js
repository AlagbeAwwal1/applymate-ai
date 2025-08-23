// Unified API helpers with:
// - auth:false to skip Authorization on public endpoints
// - auto refresh on 401 token_not_valid for protected endpoints
// - consistent JSON parsing + helpful errors

import { getAccess, getRefresh, setTokens, clearToken } from "./auth";

// Base like http://127.0.0.1:8000/api  (no trailing slash)
const API  = (import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api").replace(/\/+$/,"");
const ROOT = API.replace(/\/api$/,""); // host root, e.g. http://127.0.0.1:8000

async function refreshAccess() {
  const refresh = getRefresh();
  if (!refresh) {
    clearToken();
    throw new Error("Session expired");
  }
  const r = await fetch(`${ROOT}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!r.ok) {
    clearToken();
    throw new Error("Session expired");
  }
  const { access } = await r.json();
  setTokens({ access, refresh });
  return access;
}

function buildUrl(path) {
  return `${API}${path.startsWith("/") ? path : `/${path}`}`;
}

async function request(path, { method = "GET", headers = {}, body, auth = true } = {}) {
  const url = buildUrl(path);

  // attach token for protected calls
  if (auth) {
    const tok = getAccess();
    if (tok) headers["Authorization"] = `Bearer ${tok}`;
  }

  let res = await fetch(url, { method, headers, body });

  // Handle expired/invalid token once, then retry
  if (auth && res.status === 401) {
    const text = await res.text();
    if (text.includes('"token_not_valid"')) {
      try {
        const newTok = await refreshAccess();
        headers["Authorization"] = `Bearer ${newTok}`;
        res = await fetch(url, { method, headers, body });
      } catch {
        throw new Error("HTTP 401: Session expired");
      }
    } else {
      throw new Error(`HTTP 401: ${text}`);
    }
  }

  const raw = await res.text();
  let data = {};
  if (raw) {
    try { data = JSON.parse(raw); } catch { /* non-JSON */ data = { raw }; }
  }
  if (!res.ok) {
    // Prefer server-provided detail if present
    const msg = data?.detail ? `HTTP ${res.status}: ${data.detail}` : `HTTP ${res.status}: ${raw}`;
    throw new Error(msg);
  }
  return data;
}

// JSON convenience wrappers
const j = (m) => (p, b, opt = {}) =>
  request(p, {
    method: m,
    headers: { "Content-Type": "application/json", ...(opt.headers || {}) },
    body: b !== undefined ? JSON.stringify(b) : undefined,
    ...opt,
  });

export const jget   = (p, opt)    => request(p, { ...opt });
export const jpost  = j("POST");
export const jpatch = j("PATCH");

// -------------------- AUTH APIs (public; no Authorization header) --------------------
export async function register({ username, email, password }) {
  const r = await fetch(`${ROOT}/api/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  const txt = await r.text();
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${txt}`);
  return txt ? JSON.parse(txt) : {};
}

export async function login({ username, password }) {
  const r = await fetch(`${ROOT}/api/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const txt = await r.text();
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${txt}`);
  return txt ? JSON.parse(txt) : {};
}

// -------------------- BUSINESS APIs --------------------
// public
export const health    = () => jget("/health/", { auth: false });
export const extractJD = (payload) => jpost("/jobs/extract/", payload, { auth: false });

// protected
export const createJob = (payload) => jpost("/jobs/", payload);
export const listJobs  = (q = "") => jget(`/jobs/${q ? `?q=${encodeURIComponent(q)}` : ""}`);
export const getJob    = (id) => jget(`/jobs/${id}/`);

export const listApps  = (job_id) => jget(`/apps/${job_id ? `?job_id=${job_id}` : ""}`);
export const createApp = (payload) => jpost("/apps/", payload);
export const updateApp = (id, payload) => jpatch(`/apps/${id}/`, payload);

export const scoreFit  = (payload) => jpost("/fit/score/", payload);
export const genDoc    = (payload) => jpost("/docs/generate/", payload);

// Resumes: upload uses multipart (and token)
export async function uploadResume(file, label = "Base Resume") {
  const form = new FormData();
  form.append("label", label);
  form.append("file", file);

  const tok = getAccess();
  const r = await fetch(buildUrl("/resume/"), {
    method: "POST",
    headers: tok ? { Authorization: `Bearer ${tok}` } : {},
    body: form,
  });
  const txt = await r.text();
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${txt}`);
  return txt ? JSON.parse(txt) : {};
}

export const listResumes = () => jget("/resume/");
