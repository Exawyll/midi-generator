# MIDI.GEN — AI-Powered MIDI Arrangement Generator

![Stack](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square)
![Stack](https://img.shields.io/badge/AI-Claude%20Sonnet%204.6-blueviolet?style=flat-square)
![Stack](https://img.shields.io/badge/frontend-React%2018%20%2B%20Vite-61dafb?style=flat-square)

A local web app that uses Claude to compose full MIDI arrangements from a plain-text description.
Describe your track, pick a style and BPM, and download a `.mid` ready for GarageBand or any DAW.

→ See [midi-generator/README.md](midi-generator/README.md) for full setup, architecture, and API docs.

---

## Quick start

```bash
# 1. Create and activate a Python venv
python -m venv venv && source venv/bin/activate
pip install fastapi "uvicorn[standard]" anthropic midiutil pydantic python-dotenv

# 2. Set your Anthropic API key
cp midi-generator/.env.example midi-generator/backend/.env
# Edit midi-generator/backend/.env → ANTHROPIC_API_KEY=sk-ant-...

# 3. Launch backend + frontend together
cd midi-generator && ./start.sh
```

Open **http://localhost:5173**, describe your track, and click **▶ GENERATE**.
