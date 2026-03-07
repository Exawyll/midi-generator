import { useState } from "react";
import { generateArrangement } from "./api";
import { useAuth }         from "./components/LoginGate";
import GeneratorForm       from "./components/GeneratorForm";
import ArrangementPreview  from "./components/ArrangementPreview";
import DownloadButton      from "./components/DownloadButton";

export default function App() {
  const { onExpired } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);   // { arrangement, midi_b64 }
  const [error,   setError]   = useState(null);

  const handleGenerate = async (formData) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await generateArrangement(formData);
      setResult(data);
    } catch (err) {
      if (err.message === "SESSION_EXPIRED") {
        onExpired(); // redirect back to login
      } else {
        setError(err.message || "Unknown error");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-studio-bg text-gray-100 font-sans">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="border-b border-studio-border sticky top-0 z-10 bg-studio-bg/80 backdrop-blur">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-4">
          {/* Logo mark */}
          <div className="flex items-center gap-2">
            <Waveform />
            <span className="font-mono font-bold text-lg tracking-[0.2em] text-neon-cyan glow-cyan">
              MIDI.GEN
            </span>
          </div>
          <span className="hidden sm:block text-xs text-gray-600 font-mono border-l border-studio-border pl-4">
            AI-Powered MIDI Arrangement Generator
          </span>
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────────────── */}
      <main className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        {/* Tagline */}
        <div className="space-y-1">
          <h1 className="text-2xl font-mono font-bold text-white">
            Describe your track.{" "}
            <span className="text-neon-cyan">We'll compose the MIDI.</span>
          </h1>
          <p className="text-sm text-gray-500">
            Claude generates a full arrangement — intro, build, drop, break, outro — ready for your DAW.
          </p>
        </div>

        {/* Form */}
        <GeneratorForm onGenerate={handleGenerate} loading={loading} />

        {/* Loading skeleton */}
        {loading && <LoadingSkeleton />}

        {/* Error */}
        {error && !loading && (
          <div className="border border-red-500/40 bg-red-950/20 rounded-xl p-5 animate-fade-in">
            <div className="flex items-start gap-3">
              <span className="text-red-400 text-lg leading-none">✕</span>
              <div>
                <p className="text-sm font-mono font-bold text-red-400 mb-1">Generation failed</p>
                <p className="text-sm text-red-300/80">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div className="space-y-6">
            <ArrangementPreview arrangement={result.arrangement} />
            <DownloadButton midiB64={result.midi_b64} title={result.arrangement.title} />
          </div>
        )}
      </main>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="border-t border-studio-border mt-20">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-xs font-mono text-gray-700">MIDI.GEN · local dev build</span>
          <span className="text-xs font-mono text-gray-700">powered by Claude</span>
        </div>
      </footer>
    </div>
  );
}

/* ── Sub-components ───────────────────────────────────────── */

function Waveform() {
  const bars = [3, 6, 9, 12, 9, 6, 3, 6, 10, 7, 4, 8, 5];
  return (
    <div className="flex items-center gap-[2px] h-5">
      {bars.map((h, i) => (
        <span
          key={i}
          className="inline-block w-0.5 bg-neon-cyan rounded-full"
          style={{
            height:          `${h}px`,
            opacity:         0.6 + (h / 12) * 0.4,
            boxShadow:       `0 0 4px #00f5d480`,
            animationDelay:  `${i * 0.08}s`,
          }}
        />
      ))}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-fade-in">
      {/* Status bar */}
      <div className="flex items-center gap-3 text-xs font-mono text-neon-cyan">
        <span className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse-slow" />
        Claude is composing your arrangement...
      </div>

      {/* Fake timeline skeleton */}
      <div className="bg-studio-surface border border-studio-border rounded-xl p-5 space-y-3">
        <div className="shimmer-bg h-4 w-48 rounded" />
        <div className="shimmer-bg h-3 w-24 rounded mt-1" />

        <div className="mt-4 space-y-2">
          {[28, 20, 36, 16, 24].map((w, i) => (
            <div key={i} className="flex gap-2 items-center">
              <div className="shimmer-bg h-3 w-14 rounded" />
              <div className="shimmer-bg h-6 rounded flex-1" style={{ maxWidth: `${w}%` }} />
              <div className="shimmer-bg h-6 rounded flex-1" style={{ maxWidth: `${100 - w - 10}%` }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
