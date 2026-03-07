/**
 * LoginGate — Wraps the entire app behind a password prompt.
 * Shows a studio-themed login screen; on success stores the JWT and
 * renders children.
 */

import { useState } from "react";
import { login } from "../api";

export default function LoginGate({ children }) {
  const [authed,   setAuthed]   = useState(!!getStoredToken());
  const [password, setPassword] = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(password);
      setAuthed(true);
    } catch (err) {
      setError(err.message || "Invalid password");
      setPassword("");
    } finally {
      setLoading(false);
    }
  };

  // Session expired — 401 on /api/generate will call this via api.js
  const handleExpired = () => setAuthed(false);

  if (authed) {
    return <AuthContext.Provider value={{ onExpired: handleExpired }}>{children}</AuthContext.Provider>;
  }

  return (
    <div className="min-h-screen bg-studio-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <Waveform />
          </div>
          <h1 className="font-mono font-bold text-2xl tracking-[0.2em] text-neon-cyan glow-cyan">
            MIDI.GEN
          </h1>
          <p className="text-xs text-gray-600 font-mono tracking-widest uppercase">
            Enter password to continue
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="bg-studio-surface border border-studio-border rounded-xl p-6 space-y-4"
        >
          <div className="space-y-2">
            <label className="block text-xs font-mono font-bold tracking-widest text-neon-cyan uppercase">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              autoFocus
              disabled={loading}
              className="w-full bg-studio-bg border border-studio-border rounded-lg px-4 py-3
                         text-sm text-gray-200 placeholder-gray-700 font-mono tracking-widest
                         focus:outline-none focus:border-neon-cyan focus:ring-1 focus:ring-neon-cyan/30
                         transition-colors disabled:opacity-50"
            />
          </div>

          {error && (
            <p className="text-xs font-mono text-red-400 flex items-center gap-2">
              <span>✕</span> {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !password}
            className={`
              w-full py-3 rounded-lg font-mono font-bold tracking-widest text-sm uppercase
              transition-all duration-200
              ${loading || !password
                ? "bg-studio-muted text-gray-500 cursor-not-allowed"
                : "bg-neon-cyan text-studio-bg hover:bg-neon-cyan/90 glow-box cursor-pointer"}
            `}
          >
            {loading ? "AUTHENTICATING..." : "ENTER"}
          </button>
        </form>

        <p className="text-center text-xs text-gray-700 font-mono">
          Session valid for 24 hours
        </p>
      </div>
    </div>
  );
}

// Context so child components can trigger logout on 401
import { createContext, useContext } from "react";
export const AuthContext = createContext({ onExpired: () => {} });
export const useAuth = () => useContext(AuthContext);

// Helpers
function getStoredToken() {
  try { return localStorage.getItem("midi_gen_token"); }
  catch { return null; }
}

function Waveform() {
  const bars = [3, 6, 9, 12, 9, 6, 3, 6, 10, 7, 4, 8, 5];
  return (
    <div className="flex items-center gap-[2px] h-5">
      {bars.map((h, i) => (
        <span
          key={i}
          className="inline-block w-0.5 bg-neon-cyan rounded-full"
          style={{ height: `${h}px`, opacity: 0.5 + (h / 12) * 0.5 }}
        />
      ))}
    </div>
  );
}
