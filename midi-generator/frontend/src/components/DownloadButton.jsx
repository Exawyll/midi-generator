/**
 * DownloadButton — Decodes the base64 MIDI and triggers a browser download.
 * No server round-trip needed — all done client-side.
 */

export default function DownloadButton({ midiB64, title }) {
  const handleDownload = () => {
    // Decode base64 → Uint8Array → Blob → object URL → click
    const binary  = atob(midiB64);
    const bytes   = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    const blob = new Blob([bytes], { type: "audio/midi" });
    const url  = URL.createObjectURL(blob);

    const a      = document.createElement("a");
    a.href       = url;
    a.download   = `${slugify(title)}.mid`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Release object URL after a short delay
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };

  return (
    <div className="flex justify-center">
      <button
        onClick={handleDownload}
        className="
          group flex items-center gap-3 px-8 py-3.5
          bg-studio-surface border border-neon-cyan/40 rounded-xl
          font-mono font-bold text-sm tracking-widest text-neon-cyan uppercase
          hover:bg-neon-cyan/10 hover:border-neon-cyan transition-all duration-300
          glow-box-hover
        "
      >
        <DownloadIcon />
        Download .mid
        <span className="text-xs text-gray-500 normal-case font-normal tracking-normal font-sans">
          {slugify(title)}.mid
        </span>
      </button>
    </div>
  );
}

function DownloadIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="group-hover:translate-y-0.5 transition-transform"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function slugify(str) {
  return (str ?? "arrangement")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60);
}
