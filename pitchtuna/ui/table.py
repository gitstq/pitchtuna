"""Plain-text rendering: one-shot reports, live status lines and JSON.

The layout helpers here are pure functions (no curses), so they are easy to
unit-test and are reused by the curses screen.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..notes import (
    DEFAULT_A4,
    freq_to_note,
    midi_to_freq,
    midi_to_note,
)
from ..stability import StableState


@dataclass
class Evaluation:
    voiced: bool
    freq: float
    detected_note: str
    target_label: str
    target_note: str
    target_freq: float
    cents: float
    in_tune: bool
    locked: bool
    confidence: float
    rms: float
    clipped: bool

    @property
    def direction(self) -> str:
        if not self.voiced:
            return "silent"
        if self.in_tune:
            return "in_tune"
        return "sharp" if self.cents > 0 else "flat"


def evaluate(
    state: StableState,
    tuning,
    a4: float = DEFAULT_A4,
    in_tune_cents: float = 5.0,
) -> Evaluation:
    freq = state.freq
    if not state.voiced or freq <= 0:
        return Evaluation(
            voiced=False,
            freq=0.0,
            detected_note="-",
            target_label="-",
            target_note="-",
            target_freq=0.0,
            cents=0.0,
            in_tune=False,
            locked=False,
            confidence=state.confidence,
            rms=state.rms,
            clipped=state.clipped,
        )

    if tuning.chromatic:
        info = freq_to_note(freq, a4)
        target_note = info.name
        target_freq = midi_to_freq(info.midi, a4)
        target_label = info.name
        cents = info.cents
        detected_note = info.name
    else:
        rs, cents = tuning.nearest(freq)
        target_note = midi_to_note(rs.midi)
        target_freq = rs.freq
        target_label = rs.label
        detected_note = freq_to_note(freq, a4).name

    return Evaluation(
        voiced=True,
        freq=freq,
        detected_note=detected_note,
        target_label=target_label,
        target_note=target_note,
        target_freq=target_freq,
        cents=cents,
        in_tune=abs(cents) <= in_tune_cents,
        locked=state.locked,
        confidence=state.confidence,
        rms=state.rms,
        clipped=state.clipped,
    )


def cents_bar(cents: float, width: int = 31, span: float = 50.0) -> str:
    """A needle bar from ``-span`` to ``+span`` cents with 0 in the middle."""
    center = width // 2
    track = ["-"] * width
    track[center] = "0"
    clamped = max(-span, min(span, cents))
    idx = int(round((clamped + span) / (2 * span) * (width - 1)))
    track[idx] = "#"
    return "".join(track)


def level_bar(rms: float, width: int = 18) -> str:
    filled = int(round(min(1.0, rms / 0.5) * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def render_block(ev: Evaluation, tuning, a4: float = DEFAULT_A4) -> str:
    header = f"{tuning.instrument.emoji} {tuning.instrument.name}   A4={a4:g} Hz"
    if not ev.voiced:
        return (
            f"{header}\n"
            "──────────────────────────────────\n"
            "🎙️  Listening ... play a note near the tuner.\n"
            f"level {level_bar(ev.rms)}"
            + ("\n⚠️  Input clipping! Lower the gain." if ev.clipped else "")
        )

    if ev.direction == "in_tune":
        status = "🎯 In tune"
    elif ev.direction == "sharp":
        status = "🔺 Too sharp (high) — flatten the string"
    else:
        status = "🔻 Too flat (low) — tighten the string"
    lock = "🔒 Locked" if ev.locked else "🔓 Tracking"

    lines = [
        header,
        "──────────────────────────────────",
        f"🎵 Detected : {ev.detected_note}   ({ev.freq:7.2f} Hz)",
        f"🎯 Target   : {ev.target_label}  {ev.target_note}  ({ev.target_freq:7.2f} Hz)",
        f"📏 Cents    : {ev.cents:+6.1f}   {status}",
        f"   flat  {cents_bar(ev.cents)}  sharp",
        f"🎚️  Level {level_bar(ev.rms)}   conf {ev.confidence * 100:3.0f}%   {lock}",
    ]
    if ev.clipped:
        lines.append("⚠️  Input clipping! Lower the microphone/input gain.")
    return "\n".join(lines)


def render_json(ev: Evaluation, tuning, a4: float = DEFAULT_A4) -> dict:
    return {
        "instrument": tuning.instrument.key,
        "instrument_name": tuning.instrument.name,
        "a4": a4,
        "voiced": ev.voiced,
        "locked": ev.locked,
        "frequency_hz": round(ev.freq, 3),
        "detected_note": ev.detected_note,
        "target_label": ev.target_label,
        "target_note": ev.target_note,
        "target_frequency_hz": round(ev.target_freq, 3),
        "cents": round(ev.cents, 2),
        "direction": ev.direction,
        "in_tune": ev.in_tune,
        "confidence": round(ev.confidence, 3),
        "rms": round(ev.rms, 4),
        "clipping": ev.clipped,
    }
