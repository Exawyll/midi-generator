import { useState } from "react";

const STYLES = [
  { id: "techno",  label: "TECHNO",  desc: "Four-on-the-floor, dark, industrial" },
  { id: "house",   label: "HOUSE",   desc: "Soulful, swinging, warm" },
  { id: "minimal", label: "MINIMAL", desc: "Sparse, hypnotic, space" },
];

export default function GeneratorForm({ onGenerate, loading }) {
  const [description, setDescription] = useState("");
  const [style, setStyle]             = useState("techno");
  const [bpm, setBpm]                 = useState(130);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!description.trim()) return;
    onGenerate({ description: description.trim(), style, bpm: Number(bpm) });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-studio-surface border border-studio-border rounded-xl p-6 space-y-6"
    >
      {/* Description */}
      <div className="space-y-2">
        <label className="block text-xs font-mono font-bold tracking-widest text-neon-cyan uppercase">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="A dark, hypnotic techno track with industrial bass stabs and a driving kick..."
          rows={3}
          disabled={loading}
          className="w-full bg-studio-bg border border-studio-border rounded-lg px-4 py-3
                     text-sm text-gray-200 placeholder-gray-600 font-mono
                     focus:outline-none focus:border-neon-cyan focus:ring-1 focus:ring-neon-cyan/30
                     resize-none transition-colors disabled:opacity-50"
        />
      </div>

      {/* Style selector */}
      <div className="space-y-2">
        <label className="block text-xs font-mono font-bold tracking-widest text-neon-cyan uppercase">
          Style
        </label>
        <div className="grid grid-cols-3 gap-3">
          {STYLES.map((s) => (
            <button
              key={s.id}
              type="button"
              disabled={loading}
              onClick={() => setStyle(s.id)}
              className={`
                relative rounded-lg px-4 py-3 text-left transition-all duration-200
                border font-mono disabled:opacity-50
                ${style === s.id
                  ? "border-neon-cyan bg-neon-cyan/10 glow-box"
                  : "border-studio-border bg-studio-bg hover:border-studio-muted"}
              `}
            >
              <div
                className={`text-sm font-bold tracking-widest ${
                  style === s.id ? "text-neon-cyan" : "text-gray-300"
                }`}
              >
                {s.label}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">{s.desc}</div>
              {style === s.id && (
                <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-neon-cyan animate-pulse" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* BPM slider */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-xs font-mono font-bold tracking-widest text-neon-cyan uppercase">
            BPM
          </label>
          <span className="text-xl font-mono font-bold text-white glow-cyan tabular-nums">
            {bpm}
          </span>
        </div>
        <input
          type="range"
          min={80}
          max={180}
          step={1}
          value={bpm}
          onChange={(e) => setBpm(e.target.value)}
          disabled={loading}
          className="w-full disabled:opacity-50"
        />
        <div className="flex justify-between text-xs text-gray-600 font-mono">
          <span>80</span>
          <span>130</span>
          <span>180</span>
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading || !description.trim()}
        className={`
          w-full py-3.5 rounded-lg font-mono font-bold tracking-widest text-sm uppercase
          transition-all duration-300
          ${loading || !description.trim()
            ? "bg-studio-muted text-gray-500 cursor-not-allowed"
            : "bg-neon-cyan text-studio-bg hover:bg-neon-cyan/90 glow-box cursor-pointer"}
        `}
      >
        {loading ? <LoadingLabel /> : "▶  GENERATE"}
      </button>
    </form>
  );
}

function LoadingLabel() {
  return (
    <span className="flex items-center justify-center gap-3">
      <span className="flex gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <span
            key={i}
            className="inline-block w-0.5 bg-gray-400 rounded-full animate-pulse"
            style={{
              height: `${8 + (i % 3) * 4}px`,
              animationDelay: `${i * 0.12}s`,
            }}
          />
        ))}
      </span>
      COMPOSING...
    </span>
  );
}
