from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal, Any


class Note(BaseModel):
    pitch: int       # MIDI note number 0-127
    beat: float      # beat offset within ONE pattern cycle (quarter notes, 0-indexed)
    duration: float  # duration in quarter notes
    velocity: int    # 0-127


class Track(BaseModel):
    name: str
    instrument_type: Literal["drums", "melodic"] = "melodic"

    @field_validator("instrument_type", mode="before")
    @classmethod
    def coerce_instrument_type(cls, v: Any) -> str:
        """Accept any drums-adjacent value; coerce everything else to 'melodic'."""
        if isinstance(v, str) and v.lower() in ("drums", "drum", "percussion", "perc"):
            return "drums"
        return "melodic"
    midi_channel: int                  # 0-indexed; 9 = General MIDI drums
    midi_program: Optional[int] = None # GM program 0-127, melodic only
    # Pattern-based approach: define 1-2 bars and repeat to fill the phase.
    # Keeps the JSON compact — a 16-bar drop only needs 1 bar of notes.
    pattern_bars: int = 1              # length of one pattern cycle in bars
    pattern: List[Note] = []           # notes for one cycle (beat 0 to pattern_bars*4)


class Phase(BaseModel):
    name: str           # "intro" | "build" | "drop" | "break" | "outro"
    duration_bars: int  # total bars for this phase (pattern repeats to fill it)
    tracks: List[Track] = []


class Arrangement(BaseModel):
    title: str
    bpm: int
    style: str
    phases: List[Phase]

    @field_validator("bpm")
    @classmethod
    def bpm_range(cls, v: int) -> int:
        if not (40 <= v <= 220):
            raise ValueError("BPM must be between 40 and 220")
        return v


class GenerateRequest(BaseModel):
    description: str
    style: Literal["techno", "house", "minimal"]
    bpm: int

    @field_validator("bpm")
    @classmethod
    def bpm_range(cls, v: int) -> int:
        if not (80 <= v <= 180):
            raise ValueError("BPM must be between 80 and 180")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class GenerateResponse(BaseModel):
    arrangement: Arrangement
    midi_b64: str  # base64-encoded .mid file bytes
