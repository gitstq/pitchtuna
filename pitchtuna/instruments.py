"""Instrument presets and tuning tables.

Each preset lists the open strings of an instrument in standard tuning. The
preset stores note names; concert pitch (A4), capo and down-tuning adjustments
are resolved later into concrete frequencies by :func:`build_tuning`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .notes import cents_between, midi_to_freq, note_to_midi


@dataclass(frozen=True)
class StringSpec:
    """One open string: a human label and its base note name."""

    label: str
    note: str


@dataclass(frozen=True)
class Instrument:
    key: str
    name: str
    emoji: str
    strings: List[StringSpec] = field(default_factory=list)
    chromatic: bool = False
    description: str = ""


@dataclass(frozen=True)
class ResolvedString:
    label: str
    note: str
    midi: int
    freq: float


@dataclass(frozen=True)
class Tuning:
    """An instrument after A4 / capo / down-tuning adjustments."""

    instrument: Instrument
    a4: float
    capo: int
    tune_down: int
    strings: List[ResolvedString]

    @property
    def chromatic(self) -> bool:
        return self.instrument.chromatic

    def nearest(self, freq: float) -> Optional[tuple]:
        """Return ``(resolved_string, cents)`` for the closest open string.

        Returns ``None`` for chromatic tunings, which have no fixed strings.
        """
        if not self.strings:
            return None
        best = None
        best_cents = float("inf")
        for rs in self.strings:
            c = cents_between(freq, rs.freq)
            if abs(c) < abs(best_cents):
                best_cents = c
                best = rs
        return best, best_cents


# ---------------------------------------------------------------------------
# Preset registry
# ---------------------------------------------------------------------------
_REGISTRY: Dict[str, Instrument] = {}


def _register(instrument: Instrument) -> Instrument:
    _REGISTRY[instrument.key] = instrument
    return instrument


_register(
    Instrument(
        key="chromatic",
        name="Chromatic",
        emoji="🎹",
        chromatic=True,
        description="Twelve-tone equal-temperament tuner; recognizes every note.",
    )
)

_register(
    Instrument(
        key="guitar",
        name="Guitar (standard)",
        emoji="🎸",
        strings=[
            StringSpec("6 (low E)", "E2"),
            StringSpec("5 (A)", "A2"),
            StringSpec("4 (D)", "D3"),
            StringSpec("3 (G)", "G3"),
            StringSpec("2 (B)", "B3"),
            StringSpec("1 (high E)", "E4"),
        ],
        description="Six-string acoustic / electric guitar, E A D G B E.",
    )
)

_register(
    Instrument(
        key="guitar-dadgad",
        name="Guitar (DADGAD)",
        emoji="🎸",
        strings=[
            StringSpec("6 (D)", "D2"),
            StringSpec("5 (A)", "A2"),
            StringSpec("4 (D)", "D3"),
            StringSpec("3 (G)", "G3"),
            StringSpec("2 (A)", "A3"),
            StringSpec("1 (D)", "D4"),
        ],
        description="Celtic / fingerstyle D A D G A D alternate tuning.",
    )
)

_register(
    Instrument(
        key="bass4",
        name="Bass (4-string)",
        emoji="🎵",
        strings=[
            StringSpec("4 (low E)", "E1"),
            StringSpec("3 (A)", "A1"),
            StringSpec("2 (D)", "D2"),
            StringSpec("1 (G)", "G2"),
        ],
        description="Four-string electric bass, E A D G.",
    )
)

_register(
    Instrument(
        key="bass5",
        name="Bass (5-string)",
        emoji="🎵",
        strings=[
            StringSpec("5 (low B)", "B0"),
            StringSpec("4 (E)", "E1"),
            StringSpec("3 (A)", "A1"),
            StringSpec("2 (D)", "D2"),
            StringSpec("1 (G)", "G2"),
        ],
        description="Five-string electric bass with a low B.",
    )
)

_register(
    Instrument(
        key="bass6",
        name="Bass (6-string)",
        emoji="🎵",
        strings=[
            StringSpec("6 (low B)", "B0"),
            StringSpec("5 (E)", "E1"),
            StringSpec("4 (A)", "A1"),
            StringSpec("3 (D)", "D2"),
            StringSpec("2 (G)", "G2"),
            StringSpec("1 (high C)", "C3"),
        ],
        description="Six-string electric bass, B E A D G C.",
    )
)

_register(
    Instrument(
        key="ukulele",
        name="Ukulele (high-G)",
        emoji="🌺",
        strings=[
            StringSpec("4 (G)", "G4"),
            StringSpec("3 (C)", "C4"),
            StringSpec("2 (E)", "E4"),
            StringSpec("1 (A)", "A4"),
        ],
        description="Soprano / concert / tenor ukulele with reentrant high-G.",
    )
)

_register(
    Instrument(
        key="ukulele-lowg",
        name="Ukulele (low-G)",
        emoji="🌺",
        strings=[
            StringSpec("4 (G)", "G3"),
            StringSpec("3 (C)", "C4"),
            StringSpec("2 (E)", "E4"),
            StringSpec("1 (A)", "A4"),
        ],
        description="Ukulele with a linear low-G fourth string.",
    )
)

_register(
    Instrument(
        key="violin",
        name="Violin",
        emoji="🎻",
        strings=[
            StringSpec("4 (G)", "G3"),
            StringSpec("3 (D)", "D4"),
            StringSpec("2 (A)", "A4"),
            StringSpec("1 (E)", "E5"),
        ],
        description="Violin / mandola family treble tuning, G D A E.",
    )
)

_register(
    Instrument(
        key="mandolin",
        name="Mandolin",
        emoji="🪕",
        strings=[
            StringSpec("4 (G)", "G3"),
            StringSpec("3 (D)", "D4"),
            StringSpec("2 (A)", "A4"),
            StringSpec("1 (E)", "E5"),
        ],
        description="Mandolin courses (each pair tuned in unison), G D A E.",
    )
)

_register(
    Instrument(
        key="viola",
        name="Viola",
        emoji="🎻",
        strings=[
            StringSpec("4 (C)", "C3"),
            StringSpec("3 (G)", "G3"),
            StringSpec("2 (D)", "D4"),
            StringSpec("1 (A)", "A4"),
        ],
        description="Viola, C G D A.",
    )
)

_register(
    Instrument(
        key="cello",
        name="Cello",
        emoji="🎻",
        strings=[
            StringSpec("4 (C)", "C2"),
            StringSpec("3 (G)", "G2"),
            StringSpec("2 (D)", "D3"),
            StringSpec("1 (A)", "A3"),
        ],
        description="Violoncello, C G D A.",
    )
)

_register(
    Instrument(
        key="banjo",
        name="Banjo (5-string, open G)",
        emoji="🪕",
        strings=[
            StringSpec("5 (drone g)", "G4"),
            StringSpec("4 (D)", "D3"),
            StringSpec("3 (G)", "G3"),
            StringSpec("2 (B)", "B3"),
            StringSpec("1 (D)", "D4"),
        ],
        description="Five-string banjo with the reentrant fifth-string drone.",
    )
)


def get_instrument(key: str) -> Instrument:
    if key not in _REGISTRY:
        raise KeyError(f"Unknown instrument {key!r}")
    return _REGISTRY[key]


def list_instruments() -> List[Instrument]:
    return list(_REGISTRY.values())


def build_tuning(
    key: str,
    a4: float = 440.0,
    capo: int = 0,
    tune_down: int = 0,
) -> Tuning:
    """Resolve an instrument preset to concrete open-string frequencies.

    ``capo`` shifts every string up by the given number of semitones;
    ``tune_down`` shifts standard tuning down before the capo is applied.
    """
    instrument = get_instrument(key)
    resolved: List[ResolvedString] = []
    for spec in instrument.strings:
        midi = note_to_midi(spec.note) - tune_down + capo
        resolved.append(
            ResolvedString(
                label=spec.label,
                note=spec.note,
                midi=midi,
                freq=midi_to_freq(midi, a4),
            )
        )
    return Tuning(
        instrument=instrument,
        a4=a4,
        capo=capo,
        tune_down=tune_down,
        strings=resolved,
    )
