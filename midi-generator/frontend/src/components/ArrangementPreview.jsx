/**
 * ArrangementPreview — DAW-like timeline visualization of the arrangement.
 *
 * Layout:
 *   - Rows  = unique instruments/tracks (across all phases)
 *   - Cols  = phases (intro, build, drop, break, outro)
 *   - Cells = colored block if instrument has notes in that phase
 *   - Width = proportional to phase duration_bars
 *
 * # TODO: extend here — add a mini piano-roll inside each cell on hover
 * # TODO: extend here — add playback preview using WebMIDI or Tone.js
 */

// Instrument → neon color mapping (fallback = hashed hue)
const INSTRUMENT_COLORS = {
  kick:    "#ef4444",
  snare:   "#f97316",
  clap:    "#f97316",
  hihat:   "#eab308",
  "hi-hat": "#eab308",
  hat:     "#eab308",
  ride:    "#ca8a04",
  crash:   "#dc2626",
  tom:     "#fb923c",
  bass:    "#3b82f6",
  lead:    "#a855f7",
  melody:  "#ec4899",
  pad:     "#00f5d4",
  arp:     "#06b6d4",
  synth:   "#8b5cf6",
  chord:   "#38bdf8",
};

function getColor(name) {
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(INSTRUMENT_COLORS)) {
    if (lower.includes(key)) return color;
  }
  // Deterministic fallback color from name hash
  const hash = [...name].reduce((a, c) => a + c.charCodeAt(0), 0);
  return `hsl(${hash % 360}, 75%, 60%)`;
}

export default function ArrangementPreview({ arrangement }) {
  const { title, bpm, style, phases } = arrangement;

  // Collect unique track names preserving insertion order
  const trackNames = [];
  for (const phase of phases) {
    for (const track of phase.tracks) {
      if (!trackNames.includes(track.name)) trackNames.push(track.name);
    }
  }

  // Total bars (for proportional widths)
  const totalBars = phases.reduce((s, p) => s + p.duration_bars, 0);

  // Total pattern note count (pattern = 1-2 bar cycle, repeats to fill phase)
  const totalNotes = phases.reduce(
    (s, p) => s + p.tracks.reduce((t, tr) => t + (tr.pattern?.length ?? 0), 0),
    0
  );

  return (
    <div className="animate-slide-up space-y-4">
      {/* Header bar */}
      <div className="bg-studio-surface border border-studio-border rounded-xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-mono text-neon-cyan tracking-widest uppercase mb-1">
              Arrangement
            </p>
            <h2 className="text-lg font-mono font-bold text-white">{title}</h2>
          </div>
          <div className="flex gap-6 text-right">
            <Stat label="BPM"     value={bpm} />
            <Stat label="Style"   value={style.toUpperCase()} />
            <Stat label="Phases"  value={phases.length} />
            <Stat label="Tracks"  value={trackNames.length} />
            <Stat label="Notes"   value={totalNotes.toLocaleString()} />
          </div>
        </div>
      </div>

      {/* Phase header strip */}
      <div className="bg-studio-surface border border-studio-border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-studio-border">
          <p className="text-xs font-mono font-bold tracking-widest text-gray-500 uppercase">
            Timeline — {totalBars} bars total
          </p>
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            {/* Phase labels row */}
            <div className="flex border-b border-studio-border">
              {/* Track label column header */}
              <div className="w-28 shrink-0 px-4 py-2 text-xs font-mono text-gray-600 uppercase tracking-widest border-r border-studio-border">
                Track
              </div>
              {phases.map((phase) => {
                const widthPct = (phase.duration_bars / totalBars) * 100;
                const phaseColor = PHASE_COLORS[phase.name] ?? "#6b7280";
                return (
                  <div
                    key={phase.name}
                    className="px-3 py-2 border-r border-studio-border last:border-r-0 min-w-0"
                    style={{ width: `${widthPct}%` }}
                  >
                    <div
                      className="text-xs font-mono font-bold tracking-widest uppercase truncate"
                      style={{ color: phaseColor }}
                    >
                      {phase.name}
                    </div>
                    <div className="text-xs text-gray-600 font-mono">
                      {phase.duration_bars} bars
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Track rows */}
            {trackNames.map((trackName) => (
              <TrackRow
                key={trackName}
                name={trackName}
                phases={phases}
                totalBars={totalBars}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Phase detail cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {phases.map((phase) => (
          <PhaseCard key={phase.name} phase={phase} />
        ))}
      </div>
    </div>
  );
}

// Phase label colors
const PHASE_COLORS = {
  intro:  "#94a3b8",
  build:  "#60a5fa",
  drop:   "#00f5d4",
  break:  "#a855f7",
  outro:  "#94a3b8",
};

function TrackRow({ name, phases, totalBars }) {
  const color = getColor(name);
  return (
    <div className="flex border-b border-studio-border/50 last:border-b-0 group hover:bg-studio-bg/40 transition-colors">
      {/* Track name */}
      <div className="w-28 shrink-0 px-4 py-2.5 flex items-center gap-2 border-r border-studio-border">
        <span
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}80` }}
        />
        <span className="text-xs font-mono text-gray-300 truncate">{name}</span>
      </div>

      {/* Cells */}
      {phases.map((phase) => {
        const track = phase.tracks.find((t) => t.name === name);
        const noteCount = track?.pattern?.length ?? 0;
        const widthPct  = (phase.duration_bars / totalBars) * 100;
        const active    = noteCount > 0;

        return (
          <div
            key={phase.name}
            className="px-1.5 py-1.5 border-r border-studio-border/50 last:border-r-0 flex items-center"
            style={{ width: `${widthPct}%` }}
          >
            {active ? (
              <div
                className="w-full h-7 rounded flex items-center justify-center
                           text-xs font-mono font-bold transition-all duration-200
                           group-hover:brightness-110"
                style={{
                  backgroundColor: `${color}22`,
                  border:          `1px solid ${color}55`,
                  color:           color,
                }}
                title={`${noteCount} notes`}
              >
                <span className="hidden sm:block truncate px-1">{noteCount}n</span>
                <span
                  className="w-1 h-1 rounded-full sm:hidden"
                  style={{ backgroundColor: color }}
                />
              </div>
            ) : (
              <div className="w-full h-7 rounded bg-studio-bg/30 border border-studio-border/30" />
            )}
          </div>
        );
      })}
    </div>
  );
}

function PhaseCard({ phase }) {
  const phaseColor = PHASE_COLORS[phase.name] ?? "#6b7280";
  const totalNotes = phase.tracks.reduce((s, t) => s + (t.pattern?.length ?? 0), 0);
  const activeTracks = phase.tracks.filter((t) => (t.pattern?.length ?? 0) > 0);

  return (
    <div className="bg-studio-surface border border-studio-border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span
          className="text-xs font-mono font-bold tracking-widest uppercase"
          style={{ color: phaseColor }}
        >
          {phase.name}
        </span>
        <span className="text-xs font-mono text-gray-500">
          {phase.duration_bars} bars
        </span>
      </div>

      <div className="space-y-1.5">
        {activeTracks.map((track) => {
          const color = getColor(track.name);
          const pct   = Math.round(((track.pattern?.length ?? 0) / totalNotes) * 100);
          return (
            <div key={track.name} className="flex items-center gap-2">
              <span className="w-16 text-xs font-mono text-gray-400 truncate">{track.name}</span>
              <div className="flex-1 h-1.5 bg-studio-bg rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
              <span className="text-xs font-mono text-gray-600 w-8 text-right">
                {track.pattern?.length ?? 0}
              </span>
            </div>
          );
        })}
      </div>

      <div className="pt-1 border-t border-studio-border text-xs font-mono text-gray-600">
        {totalNotes} total notes · {activeTracks.length} tracks
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="text-xs font-mono text-gray-600 uppercase tracking-widest">{label}</div>
      <div className="text-sm font-mono font-bold text-white">{value}</div>
    </div>
  );
}
