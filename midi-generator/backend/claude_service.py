"""
claude_service.py — Calls the Claude API to generate a structured MIDI arrangement.

Modify SYSTEM_PROMPT to adjust Claude's compositional style, add new instruments,
or change the JSON schema.

# TODO: extend here — add new styles (jungle, ambient, drum&bass) in SYSTEM_PROMPT
# TODO: extend here — load prompt from an external .txt file for easier editing
"""

import json
import os
import re
import logging
import anthropic
from models import Arrangement, GenerateRequest

logger = logging.getLogger(__name__)

# Model to use — swap for claude-opus-4-6 for richer arrangements (higher cost/latency)
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")

# ---------------------------------------------------------------------------
# System prompt
# IMPORTANT: Uses a pattern-based format to stay within Claude's output token limit.
# Each track defines a short repeating pattern (1-2 bars) instead of every note.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a professional electronic music composer and MIDI programmer.
Generate a complete MIDI arrangement as compact JSON using a PATTERN-BASED format.

## CRITICAL: Output Format Rules
1. Return ONLY raw JSON — no markdown, no code fences, no explanations
2. Use the PATTERN format: define notes for 1-2 bars; they repeat to fill the phase
3. Keep it concise — a full arrangement should be ~150-400 lines of JSON

## JSON Structure

{
  "title": "Track title",
  "bpm": <integer>,
  "style": "<style>",
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
            {"pitch": 36, "beat": 0.0, "duration": 0.25, "velocity": 100},
            {"pitch": 36, "beat": 1.0, "duration": 0.25, "velocity": 95},
            {"pitch": 36, "beat": 2.0, "duration": 0.25, "velocity": 100},
            {"pitch": 36, "beat": 3.0, "duration": 0.25, "velocity": 95}
          ]
        }
      ]
    }
  ]
}

## Pattern Rules
- `pattern_bars`: how many bars the pattern covers (1 or 2)
- `pattern`: notes for ONE cycle only; beat values must be in [0, pattern_bars × 4)
- The pattern repeats automatically to fill `duration_bars`
- For 1-bar patterns: beat ∈ [0.0, 4.0)
- For 2-bar patterns: beat ∈ [0.0, 8.0)
- Use 2-bar patterns only when you need bar-2 variation (e.g. snare fill on bar 2 beat 4)

## Beat System (4/4 time)
- 1 bar = 4 quarter-note beats
- Quarter notes: 0.0, 1.0, 2.0, 3.0
- 8th notes:     0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5
- 16th notes:    0.0, 0.25, 0.5, 0.75, 1.0 ...

## Drum Map — midi_channel MUST be 9
Kick drum     = 36   Snare drum = 38   Clap        = 39
Closed hi-hat = 42   Open hi-hat = 46  Ride cymbal = 51
Crash cymbal  = 49   Hi tom = 50       Low tom     = 45

## MIDI Programs (melodic tracks)
Synth Bass 1 = 38   Synth Bass 2 = 39
Saw Lead = 81       Square Lead = 80
New Age Pad = 88    Polysynth Pad = 90
Sci-fi FX = 103

## Channel Assignments
- Channel 9: drums (REQUIRED — never change)
- Channel 0: bass
- Channel 1: lead / melody
- Channel 2: pad / chords
- Channel 3: arpeggio

## Style Patterns (copy and adapt)

### TECHNO (120–150 BPM)
Kick 1-bar pattern:    beats 0.0, 1.0, 2.0, 3.0 — velocity 100-108
Snare 1-bar pattern:   beats 1.0, 3.0 — velocity 85-92
Hi-hat 1-bar pattern:  beats 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5 — velocity 55-72
Open-hat 1-bar:        beat 3.5 only — velocity 68
Bass: short stabs 0.25 duration, minor/chromatic, pitch 28-42, velocity 85-95
Pads: long notes 2.0-4.0 duration, dark minor chords, velocity 45-60

### HOUSE (118–130 BPM)
Kick 1-bar:  beats 0.0, 1.0, 2.0, 3.0 — velocity 92-102
Clap 1-bar:  beats 1.0, 3.0 — velocity 88-96
Hi-hat 1-bar: 8th notes with swing (alternate velocity 68 / 48)
Open-hat:    beat 3.75 — velocity 62
Bass: walking line, Dorian scale, pitch 36-50, velocity 75-88
Chords: off-beat stabs (beat 0.5, 2.5), velocity 55-70

### MINIMAL (122–138 BPM)
Kick 1-bar:  beats 0.0, 2.0 only — velocity 82-92
Snare 1-bar: beat 2.0 only — velocity 72-80
Hi-hat 1-bar: sparse 16th notes (4-6 out of 16) — velocity 38-55
Bass: very sparse, long notes (1.0-2.0 duration), low register (pitch 28-40)
Pads: ambient, slow, very low velocity 35-52

## Phase Guidelines
intro  → 8 bars  → 1-2 tracks only (kick + bass or kick only)
build  → 16 bars → add hi-hat, then bass, then pad progressively
drop   → 16 bars → ALL tracks active, maximum energy
break  → 8 bars  → remove kick/snare, keep pad+bass only
outro  → 8 bars  → mirror intro, sparse

## Hard Limits — RESPECT THESE or the response will be too large
- Maximum 5 tracks per phase
- Maximum 16 notes per pattern (per track)
- Use pattern_bars: 1 whenever possible; use 2 only if essential
- Prefer reusing the same tracks across phases (same names) — vary only velocity/notes

## Final Reminder
- Return ONLY the JSON object, starting with { and ending with }
- No text before or after
- Validate that all beat values are within [0, pattern_bars × 4)"""


def generate_arrangement(request: GenerateRequest) -> Arrangement:
    """
    Calls Claude to generate a JSON arrangement, parses into an Arrangement model.
    Raises ValueError with a clear message on invalid output.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_message = (
        f"Style: {request.style} | BPM: {request.bpm}\n"
        f"Description: {request.description}\n\n"
        "Generate the arrangement JSON now. Start immediately with { and end with }."
    )

    logger.info(f"Calling Claude ({CLAUDE_MODEL}) — {request.style} @ {request.bpm} BPM")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    logger.debug(f"Claude response: {len(raw)} chars, stop_reason={response.stop_reason}")

    if response.stop_reason == "max_tokens":
        raise ValueError(
            "Claude's response was truncated (max_tokens reached). "
            "Try a shorter description or reduce the arrangement complexity."
        )

    raw = _strip_code_fence(raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        preview = raw[:400].replace("\n", " ")
        raise ValueError(
            f"Claude returned invalid JSON: {e}\n"
            f"Response preview: {preview}"
        )

    try:
        arrangement = Arrangement(**data)
    except Exception as e:
        raise ValueError(f"Claude returned an invalid arrangement structure: {e}")

    total_tracks = sum(len(p.tracks) for p in arrangement.phases)
    total_notes  = sum(
        len(t.pattern)
        for p in arrangement.phases
        for t in p.tracks
    )
    logger.info(
        f"'{arrangement.title}' — {len(arrangement.phases)} phases, "
        f"{total_tracks} track-instances, {total_notes} pattern notes"
    )
    return arrangement


def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if Claude added them."""
    match = re.match(r"^```(?:json)?\s*\n(.*)\n```\s*$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
