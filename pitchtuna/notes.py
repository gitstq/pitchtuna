"""Musical theory primitives: note names, MIDI numbers, frequencies and cents.

Everything is built on 12-tone equal temperament (12-TET), with a configurable
concert pitch (A4 frequency). Units are always stated explicitly:

* frequency -> hertz (Hz)
* MIDI note -> integer, where A4 == 69
* cents -> 1/100 of a semitone; 1200 cents == one octave
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List

# Pitch-class names, index 0 == C.
SHARPS: List[str] = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLATS: List[str] = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Semitone offset of each natural letter within an octave.
_LETTER_OFFSET = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

A4_MIDI = 69
DEFAULT_A4 = 440.0

_NOTE_RE = re.compile("^([A-Ga-g])([#b\u266f\u266dx]{0,2})(-?\d+)$")
_ACCIDENTAL_ALIASES = {"\u266f": "#", "\u266d": "b"}


@dataclass(frozen=True)
class NoteInfo:
    """The nearest discrete note to a measured frequency."""

    freq: float
    midi: int
    cents: float
    name: str
    flat_name: str
    pitch_class: str
    flat_pitch_class: str
    octave: int


def _accidental_semitones(accidental: str) -> int:
    text = "".join(_ACCIDENTAL_ALIASES.get(ch, ch) for ch in accidental)
    # "#" = +1, "b" = -1, "x" = double sharp = +2
    return text.count("#") - text.count("b") + 2 * text.count("x")


def note_to_midi(note: str) -> int:
    """Convert a note name such as ``"C#4"`` or ``"Eb2"`` to a MIDI number."""
    match = _NOTE_RE.match(note.strip())
    if not match:
        raise ValueError(f"Unrecognized note name: {note!r}")
    letter, accidental, octave = match.groups()
    midi = (int(octave) + 1) * 12 + _LETTER_OFFSET[letter.upper()]
    midi += _accidental_semitones(accidental)
    return midi


def midi_to_note(midi: int, prefer_flats: bool = False) -> str:
    """Convert a MIDI number to a note name in the chosen accidental style."""
    names = FLATS if prefer_flats else SHARPS
    pitch_class = int(round(midi)) % 12
    octave = int(round(midi)) // 12 - 1
    return f"{names[pitch_class]}{octave}"


def midi_to_freq(midi: float, a4: float = DEFAULT_A4) -> float:
    """Frequency in Hz for a (possibly fractional) MIDI number."""
    return a4 * 2.0 ** ((midi - A4_MIDI) / 12.0)


def note_to_freq(note: str, a4: float = DEFAULT_A4) -> float:
    """Frequency in Hz for a note name."""
    return midi_to_freq(note_to_midi(note), a4)


def freq_to_midi(freq: float, a4: float = DEFAULT_A4) -> float:
    """Continuous MIDI number for a frequency (may be negative below C0)."""
    if freq <= 0:
        raise ValueError("Frequency must be positive")
    return A4_MIDI + 12.0 * math.log2(freq / a4)


def freq_to_note(freq: float, a4: float = DEFAULT_A4) -> NoteInfo:
    """Snap a frequency to the nearest note and report the cents deviation."""
    midi_float = freq_to_midi(freq, a4)
    midi = int(round(midi_float))
    cents = (midi_float - midi) * 100.0
    pitch_class = midi % 12
    octave = midi // 12 - 1
    return NoteInfo(
        freq=freq,
        midi=midi,
        cents=cents,
        name=f"{SHARPS[pitch_class]}{octave}",
        flat_name=f"{FLATS[pitch_class]}{octave}",
        pitch_class=SHARPS[pitch_class],
        flat_pitch_class=FLATS[pitch_class],
        octave=octave,
    )


def cents_between(freq: float, target_freq: float) -> float:
    """Signed distance in cents from ``freq`` to ``target_freq``.

    Positive means the measured frequency is sharper (higher) than the target.
    """
    return 1200.0 * math.log2(freq / target_freq)


def freq_to_note_name(freq: float, prefer_flats: bool = False, a4: float = DEFAULT_A4) -> str:
    """Convenience: nearest note name only."""
    info = freq_to_note(freq, a4)
    return info.flat_name if prefer_flats else info.name
