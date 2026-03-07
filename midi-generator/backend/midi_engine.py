"""
midi_engine.py — Converts an Arrangement model into a .mid file (bytes).

Uses a pattern-based approach: each track defines a short pattern (1-2 bars)
that repeats automatically to fill the phase duration. This matches the compact
JSON format returned by Claude.

# TODO: extend here — add time signature changes per phase
# TODO: extend here — add velocity humanization / micro-timing offsets
# TODO: extend here — export as Ableton Live Set (.als)
"""

import io
import logging
from midiutil import MIDIFile
from models import Arrangement

logger = logging.getLogger(__name__)


def arrangement_to_midi(arrangement: Arrangement) -> bytes:
    """
    Convert an Arrangement into a multi-track MIDI file.

    Each unique track name gets its own MIDI track. Within each phase,
    the track's `pattern` repeats `floor(duration_bars / pattern_bars)` times.

    Returns raw bytes of the .mid file.
    """
    # Collect ordered unique track names — determines MIDI track layout
    track_names: list[str] = []
    for phase in arrangement.phases:
        for track in phase.tracks:
            if track.name not in track_names:
                track_names.append(track.name)

    if not track_names:
        raise ValueError("Arrangement has no tracks — cannot generate MIDI file")

    num_tracks = len(track_names)
    logger.info(f"Building MIDI: {num_tracks} tracks, BPM={arrangement.bpm}")

    midi = MIDIFile(num_tracks)

    # Set tempo on every track at time 0
    for i in range(num_tracks):
        midi.addTempo(i, 0, arrangement.bpm)

    # Track which tracks have had their program change set (first occurrence wins)
    program_changes_set: set[str] = set()

    time_offset = 0.0  # absolute beat position from start of the file

    for phase in arrangement.phases:
        phase_beats = phase.duration_bars * 4  # total beats in this phase

        for track in phase.tracks:
            track_idx = track_names.index(track.name)

            # Set GM instrument program for melodic tracks (once per track)
            if (
                track.instrument_type == "melodic"
                and track.midi_program is not None
                and track.name not in program_changes_set
            ):
                midi.addProgramChange(
                    track_idx,
                    track.midi_channel,
                    0,
                    track.midi_program,
                )
                program_changes_set.add(track.name)

            if not track.pattern:
                continue

            pattern_beats = track.pattern_bars * 4
            # How many full pattern cycles fit in this phase
            repeats = max(1, phase.duration_bars // track.pattern_bars)

            skipped = 0
            for rep in range(repeats):
                rep_offset = rep * pattern_beats

                for note in track.pattern:
                    # Note beat is relative to one pattern cycle
                    if note.beat < 0 or note.beat >= pattern_beats:
                        skipped += 1
                        continue

                    pitch    = max(0, min(127, note.pitch))
                    velocity = max(1, min(127, note.velocity))
                    duration = max(0.0625, note.duration)
                    abs_time = time_offset + rep_offset + note.beat

                    midi.addNote(
                        track_idx,
                        track.midi_channel,
                        pitch,
                        abs_time,
                        duration,
                        velocity,
                    )

            if skipped:
                logger.warning(
                    f"Phase '{phase.name}' / track '{track.name}': "
                    f"skipped {skipped} out-of-bounds notes"
                )

        time_offset += phase_beats

    buffer = io.BytesIO()
    midi.writeFile(buffer)
    midi_bytes = buffer.getvalue()

    logger.info(f"MIDI file generated: {len(midi_bytes)} bytes")
    return midi_bytes
