# MIDI.GEN — AI-Powered MIDI Arrangement Generator

A local web app that uses Claude to compose full MIDI arrangements from a plain-text description.
Describe your track, pick a style and BPM, and download a `.mid` ready for GarageBand or any DAW.

![Stack](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square)
![Stack](https://img.shields.io/badge/AI-Claude%20Sonnet%204.6-blueviolet?style=flat-square)
![Stack](https://img.shields.io/badge/frontend-React%2018%20%2B%20Vite-61dafb?style=flat-square)

---

## How it works

1. You fill in a description, choose a style (Techno / House / Minimal) and set BPM
2. Claude composes a structured arrangement (intro → build → drop → break → outro) as JSON
3. The backend converts the JSON into a `.mid` file using `midiutil`
4. The frontend displays a DAW-like timeline preview and lets you download the file

Claude uses a **pattern-based format**: it defines a 1-2 bar repeating pattern per instrument,
which the engine tiles automatically — keeping generation fast and the JSON compact.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup

### 1. Python environment

The project uses a shared venv at the repo root (`../venv` relative to `midi-generator/`).

```bash
# From the repo root (techno-ai/)
python -m venv venv
source venv/bin/activate
pip install fastapi "uvicorn[standard]" anthropic midiutil pydantic python-dotenv
```

### 2. Environment variables

```bash
cd midi-generator
cp .env.example backend/.env
# Edit backend/.env and set:  ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Start everything

```bash
./start.sh
```

`start.sh` launches both services in parallel with unified, color-coded logs:

```
[backend]   INFO:     Uvicorn running on http://127.0.0.1:8000
[frontend]  VITE v5.x  ready in 300ms → http://localhost:5173
```

Press `Ctrl+C` to stop both.

> **Manual start** (two terminals):
> ```bash
> # Terminal 1
> cd backend && uvicorn main:app --reload
> # Terminal 2
> cd frontend && npm install && npm run dev
> ```

---

## Usage

1. Open **http://localhost:5173**
2. Describe your track — *"Dark warehouse techno, industrial bass stabs, relentless kick"*
3. Select a style and set BPM
4. Click **▶ GENERATE** — Claude composes the arrangement (~15–30s)
5. Review the timeline: rows = instruments, columns = phases, block width ∝ bar count
6. Click **Download .mid** — the file is reconstructed client-side from base64

---

## Architecture

```
midi-generator/
├── backend/
│   ├── main.py              # FastAPI — POST /api/generate
│   ├── claude_service.py    # Claude API → Arrangement JSON
│   ├── midi_engine.py       # Arrangement JSON → .mid bytes (pattern tiling)
│   └── models.py            # Pydantic models (Arrangement, Phase, Track, Note)
├── frontend/
│   ├── index.html           # Tailwind CDN + custom dark/neon theme
│   ├── src/
│   │   ├── App.jsx                         # Root — state, loading, error
│   │   ├── api.js                          # fetch wrapper for /api/generate
│   │   └── components/
│   │       ├── GeneratorForm.jsx           # Description / style / BPM form
│   │       ├── ArrangementPreview.jsx      # DAW-like timeline + phase cards
│   │       └── DownloadButton.jsx          # base64 → .mid browser download
│   ├── package.json
│   └── vite.config.js       # Proxies /api/* → localhost:8000
├── start.sh                 # One-command launcher (unified logs)
├── .env.example
└── README.md
```

### API contract

```
POST /api/generate
Content-Type: application/json

{
  "description": "string",
  "style": "techno" | "house" | "minimal",
  "bpm": 80–180
}

→ 200 OK
{
  "arrangement": {
    "title": "string",
    "bpm": 140,
    "style": "techno",
    "phases": [
      {
        "name": "intro",
        "duration_bars": 8,
        "tracks": [
          {
            "name": "kick",
            "instrument_type": "drums",
            "midi_channel": 9,
            "pattern_bars": 1,
            "pattern": [
              { "pitch": 36, "beat": 0.0, "duration": 0.25, "velocity": 108 }
            ]
          }
        ]
      }
    ]
  },
  "midi_b64": "<base64-encoded .mid file>"
}
```

### Pattern tiling (midi_engine.py)

Each track defines a short pattern (`pattern_bars` × 4 beats).
The engine repeats it `duration_bars / pattern_bars` times to fill the phase,
then advances the absolute beat offset before the next phase.

---

## Extending

### Add a new style

1. `claude_service.py` — add a reference pattern block in `SYSTEM_PROMPT` under *Style Patterns*
2. `GeneratorForm.jsx` — add an entry to the `STYLES` array
3. `models.py` — extend the `Literal["techno", "house", "minimal"]` union on `GenerateRequest`

### Add new instruments

Edit the drum map table and channel assignments in `SYSTEM_PROMPT` (`claude_service.py`).

### Use a more powerful model

```bash
# backend/.env
CLAUDE_MODEL=claude-opus-4-6
```

Richer arrangements, higher cost and latency.

### Export to Ableton Live

`midi_engine.py` is fully decoupled — add an `arrangement_to_als()` function using `abletonparsing` or raw XML.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY not set` | Create `backend/.env` from `.env.example` and restart |
| `uvicorn not found` | Install deps: `venv/bin/pip install fastapi "uvicorn[standard]" anthropic midiutil pydantic` |
| CORS error in browser | Confirm backend runs on port 8000 (`./start.sh` does this automatically) |
| Generation fails — truncated JSON | Claude hit the token limit; try a shorter description |
| `.mid` silent in GarageBand | Check that the file is > 0 bytes; some arrangements need a retry |
| Frontend blank page | Run `npm install` inside `frontend/` |
