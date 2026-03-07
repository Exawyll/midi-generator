/**
 * api.js — All calls to the FastAPI backend.
 * Vite proxies /api/* and /auth/* → http://localhost:8000
 */

const BASE = "";
const TOKEN_KEY = "midi_gen_token";

// ── Token helpers ─────────────────────────────────────────────────────────────

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); }
  catch { return null; }
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeader() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Auth ──────────────────────────────────────────────────────────────────────

/**
 * Log in with the shared password.
 * Stores the returned JWT; throws on wrong password.
 */
export async function login(password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Invalid password");
  }

  const { token } = await res.json();
  setToken(token);
}

// ── API calls ─────────────────────────────────────────────────────────────────

/**
 * Generate a MIDI arrangement from a text description.
 *
 * @param {{ description: string, style: string, bpm: number }} params
 * @returns {Promise<{ arrangement: object, midi_b64: string }>}
 * @throws {Error} — includes "SESSION_EXPIRED" message on 401 so LoginGate can react
 */
export async function generateArrangement({ description, style, bpm }) {
  const res = await fetch(`${BASE}/api/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ description, style, bpm }),
  });

  if (res.status === 401) {
    clearToken();
    throw new Error("SESSION_EXPIRED");
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const err = await res.json(); detail = err.detail ?? detail; } catch {}
    throw new Error(detail);
  }

  return res.json();
}
