/**
 * api.js — All calls to the FastAPI backend.
 * Vite proxies /api/* → http://localhost:8000 (see vite.config.js).
 */

const BASE = "/api";

/**
 * Generate a MIDI arrangement from a text description.
 *
 * @param {{ description: string, style: string, bpm: number }} params
 * @returns {Promise<{ arrangement: object, midi_b64: string }>}
 * @throws {Error} with a human-readable message on any failure
 */
export async function generateArrangement({ description, style, bpm }) {
  const res = await fetch(`${BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description, style, bpm }),
  });

  if (!res.ok) {
    // Try to parse a structured error from FastAPI
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch {
      // response wasn't JSON, keep status code message
    }
    throw new Error(detail);
  }

  return res.json();
}
