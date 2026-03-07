#!/usr/bin/env python3
"""
generate.py — Generateur de musique techno par IA
Usage: python generate.py "description" [--bpm 130] [--style techno|house|minimal] [--output out.mid]
"""

import os
import sys
import json
import argparse
import anthropic
from midiutil import MIDIFile

# -- MIDI Constants --
CH_PERCU = 9
CH_BASSE = 0
CH_SYNTH = 1

KICK  = 36
SNARE = 38
HIHAT = 42

C1 = 39
C2 = 48
C3 = 60
D3 = 62
E3 = 64

VALID_PHASES = {"intro", "build", "drop", "break", "outro"}

# General MIDI program numbers embedded in the .mid file.
# GarageBand reads these on import and selects a matching instrument.
# Channel 9 (drums/clap) ignores program changes — always percussion in GM.
GM_PROGRAMS = {
    #                basse  synth
    "techno":   {"basse": 38, "synth": 81},   # Synth Bass 1 / Lead 2 Sawtooth
    "house":    {"basse": 33, "synth":  4},   # Electric Bass / Electric Piano 1
    "minimal":  {"basse": 38, "synth": 80},   # Synth Bass 1 / Lead 1 Square
}

# -------------------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------------------
SYSTEM_PROMPT = """\
You are an expert electronic music arranger and GarageBand sound designer.
Your job is to output a single JSON object with two keys: "arrangement" and "instruments".

RULES (strictly follow all of them):
- Output ONLY a raw JSON object. No markdown, no code blocks, no explanation, no comments.
- The top-level object must have exactly two keys: "arrangement" and "instruments".

"arrangement" rules:
- A JSON array where each element has exactly these fields:
  {"mesure": <int>, "phase": <str>, "drums": <bool>, "basse": <bool>, "synth": <bool>, "clap": <bool>}
- "mesure" starts at 1 and increments by 1 with no gaps.
- "phase" must be one of: "intro", "build", "drop", "break", "outro"
- Maximum 32 mesures total.
- The arrangement must feel musical and match the user's description.

"instruments" rules:
- A JSON object with exactly four keys: "drums", "basse", "synth", "clap"
- Each value is an object with two fields:
    "name": a descriptive label for the track (e.g. "Dark Kick", "Sub Bass", "Acid Lead")
    "gm_program": an integer (0-127) — the General MIDI program number that best matches
      the sound. This will be embedded in the MIDI file so GarageBand selects the right instrument.
- drums and clap are on the GM percussion channel (channel 10), so set "gm_program" to null for them.
- For basse, use GM programs 32-39 (bass family): 32=Acoustic Bass, 33=Electric Bass, 38=Synth Bass 1, 39=Synth Bass 2
- For synth, use GM programs 80-87 (synth lead family): 80=Lead Square, 81=Lead Sawtooth, 82=Lead Calliope, 87=Lead Bass+Lead

EXAMPLES BY STYLE:
techno  → drums: {name:"Dark Kick",     gm_program:null}, basse: {name:"Stinger Bass",   gm_program:38}, synth: {name:"Acid Lead",          gm_program:81}, clap: {name:"Industrial Snap", gm_program:null}
house   → drums: {name:"House Kit",     gm_program:null}, basse: {name:"Detroit Bass",    gm_program:33}, synth: {name:"Electric Piano",     gm_program:4},  clap: {name:"Room Clap",       gm_program:null}
minimal → drums: {name:"Minimal Kick",  gm_program:null}, basse: {name:"Sub Bass",        gm_program:38}, synth: {name:"Square Lead",        gm_program:80}, clap: {name:"Tight Clap",      gm_program:null}

Adapt choices to the mood of the description (dark, euphoric, industrial, groovy, etc.).

TYPICAL ARRANGEMENT STRUCTURES:
- intro: drums only (no basse, no synth, no clap)
- build: drums + basse, building tension
- drop: all elements active (drums + basse + synth + clap)
- break: drums only or stripped back, tension release
- outro: gradual removal of elements

Output the JSON object now.\
"""

# -------------------------------------------------------
# MIDI ENGINE
# -------------------------------------------------------
def add_perc(midi, temps, note, volume=100):
    midi.addNote(0, CH_PERCU, note, temps, 0.25, volume)

def add_basse(midi, temps, note, duree=0.9, volume=95):
    midi.addNote(1, CH_BASSE, note, temps, duree, volume)

def add_synth(midi, temps, note, duree=0.25, volume=85):
    midi.addNote(2, CH_SYNTH, note, temps, duree, volume)

def add_clap(midi, temps, note, duree=0.25, volume=85):
    midi.addNote(3, CH_PERCU, note, temps, duree, volume)

def pattern_drums(midi, offset):
    for t in [0, 1, 2, 3]:
        add_perc(midi, offset + t, KICK, volume=110)
    for t in [1, 3]:
        add_perc(midi, offset + t, SNARE, volume=90)
    for t in [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]:
        add_perc(midi, offset + t, HIHAT, volume=70)

def pattern_basse(midi, offset):
    for t in [0, 1, 2, 3]:
        add_basse(midi, offset + t, C2)

def pattern_synth(midi, offset):
    motif = [
        (0,   C3), (0.5, C3),
        (1,   D3), (1.5, C3),
        (2,   E3), (2.5, C3),
        (3,   D3), (3.5, E3),
    ]
    for t, note in motif:
        add_synth(midi, offset + t, note)

def pattern_clap(midi, offset):
    for t in [1, 3]:
        add_clap(midi, offset + t, 39, volume=100)

def generate_midi(arrangement, bpm, output_path, instruments=None):
    midi = MIDIFile(4)
    for piste in range(4):
        midi.addTempo(piste, 0, bpm)

    # Track names (visible as labels in GarageBand)
    track_names = {0: "Drums", 1: "Basse", 2: "Synth", 3: "Clap"}
    if instruments:
        track_names[0] = instruments["drums"]["name"]
        track_names[1] = instruments["basse"]["name"]
        track_names[2] = instruments["synth"]["name"]
        track_names[3] = instruments["clap"]["name"]
    for track, name in track_names.items():
        midi.addTrackName(track, 0, name)

    # Program Change messages for melodic tracks — GarageBand reads these on import
    if instruments:
        gm_basse = instruments["basse"].get("gm_program")
        gm_synth = instruments["synth"].get("gm_program")
        if gm_basse is not None:
            midi.addProgramChange(1, CH_BASSE, 0, int(gm_basse))
        if gm_synth is not None:
            midi.addProgramChange(2, CH_SYNTH, 0, int(gm_synth))

    for bloc in arrangement:
        offset = (bloc["mesure"] - 1) * 4
        phase  = bloc["phase"]

        if bloc["drums"]:
            pattern_drums(midi, offset)
        if bloc["basse"]:
            pattern_basse(midi, offset)
        if bloc["synth"]:
            pattern_synth(midi, offset)
        if bloc["clap"]:
            pattern_clap(midi, offset)

        print(f"  Mesure {bloc['mesure']:2d} [{phase:<7}] "
              f"drums={'ok' if bloc['drums'] else '--'} "
              f"basse={'ok' if bloc['basse'] else '--'} "
              f"synth={'ok' if bloc['synth'] else '--'} "
              f"clap={'ok' if bloc['clap'] else '--'}")

    with open(output_path, "wb") as f:
        midi.writeFile(f)

# -------------------------------------------------------
# VALIDATION
# -------------------------------------------------------
def validate_response(data):
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object with 'arrangement' and 'instruments' keys")
    if "arrangement" not in data:
        raise ValueError("Missing key 'arrangement'")
    if "instruments" not in data:
        raise ValueError("Missing key 'instruments'")

    arrangement = data["arrangement"]
    if not isinstance(arrangement, list) or len(arrangement) == 0:
        raise ValueError("'arrangement' must be a non-empty array")
    if len(arrangement) > 32:
        raise ValueError(f"Too many mesures: {len(arrangement)} (max 32)")

    for i, bloc in enumerate(arrangement):
        required = {"mesure", "phase", "drums", "basse", "synth", "clap"}
        missing = required - set(bloc.keys())
        if missing:
            raise ValueError(f"Bloc {i+1} missing fields: {missing}")
        if bloc["phase"] not in VALID_PHASES:
            raise ValueError(f"Bloc {i+1} invalid phase: '{bloc['phase']}'")
        if bloc["mesure"] != i + 1:
            raise ValueError(f"Bloc {i+1} has mesure={bloc['mesure']} (expected {i+1})")
        for field in ["drums", "basse", "synth", "clap"]:
            if not isinstance(bloc[field], bool):
                raise ValueError(f"Bloc {i+1}: '{field}' must be a boolean")

    instruments = data["instruments"]
    if not isinstance(instruments, dict):
        raise ValueError("'instruments' must be an object")
    for key in ["drums", "basse", "synth", "clap"]:
        if key not in instruments:
            raise ValueError(f"'instruments' missing key '{key}'")
        inst = instruments[key]
        if not isinstance(inst, dict):
            raise ValueError(f"'instruments.{key}' must be an object with 'name' and 'gm_program'")
        if not isinstance(inst.get("name"), str) or not inst["name"].strip():
            raise ValueError(f"'instruments.{key}.name' must be a non-empty string")
        gm = inst.get("gm_program")
        if gm is not None and not isinstance(gm, int):
            raise ValueError(f"'instruments.{key}.gm_program' must be an integer or null")

# -------------------------------------------------------
# CLAUDE API
# -------------------------------------------------------
FALLBACK_RESPONSE = {
    "arrangement": [
        {"mesure": 1,  "phase": "intro",  "drums": True,  "basse": False, "synth": False, "clap": False},
        {"mesure": 2,  "phase": "intro",  "drums": True,  "basse": False, "synth": False, "clap": False},
        {"mesure": 3,  "phase": "build",  "drums": True,  "basse": True,  "synth": False, "clap": False},
        {"mesure": 4,  "phase": "build",  "drums": True,  "basse": True,  "synth": False, "clap": False},
        {"mesure": 5,  "phase": "drop",   "drums": True,  "basse": True,  "synth": True,  "clap": True},
        {"mesure": 6,  "phase": "drop",   "drums": True,  "basse": True,  "synth": True,  "clap": True},
        {"mesure": 7,  "phase": "drop",   "drums": True,  "basse": True,  "synth": True,  "clap": True},
        {"mesure": 8,  "phase": "drop",   "drums": True,  "basse": True,  "synth": True,  "clap": True},
    ],
    "instruments": {
        "drums": {"name": "Deep Tech",        "gm_program": None},
        "basse": {"name": "Stinger Bass",     "gm_program": 38},
        "synth": {"name": "Analog Mono Lead", "gm_program": 81},
        "clap":  {"name": "Big Bump",         "gm_program": None},
    },
}

def call_claude(description, style, bpm, max_retries=2):
    client = anthropic.Anthropic()

    user_message = f"Style: {style} | BPM: {bpm}\nDescription: {description}"

    for attempt in range(1, max_retries + 2):
        print(f"[Claude] Tentative {attempt}/{max_retries + 1}...")
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            raw = message.content[0].text.strip()

            # Strip accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data = json.loads(raw)
            validate_response(data)
            return data, False  # (response, is_fallback)

        except json.JSONDecodeError as e:
            print(f"[Erreur] JSON invalide: {e}")
        except ValueError as e:
            print(f"[Erreur] Validation echouee: {e}")
        except anthropic.APIError as e:
            print(f"[Erreur] API Claude: {e}")
            break  # No point retrying on API errors

    print("[Fallback] Utilisation de l'arrangement par defaut.")
    return FALLBACK_RESPONSE, True

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generateur de musique techno par IA")
    parser.add_argument("description", help='Description en langage naturel (ex: "techno 16 mesures drop massif")')
    parser.add_argument("--bpm",    type=int, default=130, help="Tempo en BPM (defaut: 130)")
    parser.add_argument("--style",  choices=["techno", "house", "minimal"], default="techno", help="Style musical (defaut: techno)")
    parser.add_argument("--output", default=None, help="Nom du fichier de sortie (defaut: auto)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[Erreur] Variable ANTHROPIC_API_KEY non definie.")
        sys.exit(1)

    print(f"\n=== Generateur Techno IA ===")
    print(f"Description : {args.description}")
    print(f"Style       : {args.style}")
    print(f"BPM         : {args.bpm}")
    print()

    response, is_fallback = call_claude(args.description, args.style, args.bpm)

    arrangement = response["arrangement"]
    instruments = response["instruments"]
    nb_mesures  = len(arrangement)
    output_path = args.output or f"output_{args.style}_{nb_mesures}mesures_{args.bpm}bpm.mid"

    print(f"\n--- Instruments GarageBand ---")
    for key in ["drums", "basse", "synth", "clap"]:
        inst = instruments[key]
        gm   = inst["gm_program"]
        gm_str = f"  [GM program {gm}]" if gm is not None else "  [percussion channel]"
        print(f"  {key:<6}: {inst['name']}{gm_str}")

    print(f"\n--- Arrangement ({nb_mesures} mesures) ---")
    generate_midi(arrangement, args.bpm, output_path, instruments=instruments)

    status = " [FALLBACK]" if is_fallback else ""
    print(f"\nFichier genere : {output_path}{status}")
    print(f"{nb_mesures} mesures | {args.style} | {args.bpm} BPM")

if __name__ == "__main__":
    main()
