from midiutil import MIDIFile

# -- Configuration --
BPM = 125

# -- Canaux MIDI --
CH_PERCU = 9
CH_BASSE = 0
CH_SYNTH = 1

# -- Notes percussions --
KICK  = 36
SNARE = 38
HIHAT = 42

# -- Notes mélodiques --
C1 = 39
C2 = 48
C3 = 60
D3 = 62
E3 = 64

# -------------------------------------------------------
# ARRANGEMENT — décris ton morceau ici !
# Chaque ligne = une mesure
# -------------------------------------------------------
ARRANGEMENT = [
    {"mesure": 1,  "phase": "intro",  "drums": True,  "basse": False, "synth": False, "clap": False},
    {"mesure": 2,  "phase": "intro",  "drums": True,  "basse": False, "synth": False, "clap": False},
    {"mesure": 3,  "phase": "build",  "drums": True,  "basse": True,  "synth": False, "clap": False},
    {"mesure": 4,  "phase": "build",  "drums": True,  "basse": True,  "synth": False, "clap": False},
    {"mesure": 5,  "phase": "drop",   "drums": True,  "basse": True,  "synth": True , "clap": True},
    {"mesure": 6,  "phase": "drop",   "drums": True,  "basse": True,  "synth": True , "clap": True},
    {"mesure": 7,  "phase": "break",  "drums": True,  "basse": False, "synth": False, "clap": False},
    {"mesure": 8,  "phase": "break",  "drums": True,  "basse": False, "synth": False, "clap": False},
    {"mesure": 9,  "phase": "drop",   "drums": True,  "basse": True,  "synth": True , "clap": True},
    {"mesure": 10, "phase": "drop",   "drums": True,  "basse": True,  "synth": True , "clap": True},
    {"mesure": 11, "phase": "outro",  "drums": True,  "basse": True,  "synth": False, "clap": False},
    {"mesure": 12, "phase": "outro",  "drums": True,  "basse": False, "synth": False, "clap": False},
]

MESURES = len(ARRANGEMENT)

# -------------------------------------------------------
# PATTERNS
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
    for t in [1, 3]:  # temps 2 et 4 uniquement
        add_clap(midi, offset + t, 39, volume=100)

# -------------------------------------------------------
# GÉNÉRATION
# -------------------------------------------------------
midi = MIDIFile(4)
for piste in range(4):
    midi.addTempo(piste, 0, BPM)

for bloc in ARRANGEMENT:
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
          f"drums={'✅' if bloc['drums'] else '⬜'} "
          f"basse={'✅' if bloc['basse'] else '⬜'} "
          f"synth={'✅' if bloc['synth'] else '⬜'} "
          f"clap={'✅' if bloc['clap'] else '⬜'}")

# -------------------------------------------------------
# EXPORT
# -------------------------------------------------------
with open("techno_beat_TEST.mid", "wb") as f:
    midi.writeFile(f)

print(f"\n✅ techno_beat_TEST.mid généré — {MESURES} mesures à {BPM} BPM")