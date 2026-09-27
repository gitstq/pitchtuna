"""Temporal smoothing and "lock" logic.

A tuner should not jump at every noisy frame. This tracker keeps a short
window of recent estimates (in semitones), reports a median-smoothed
frequency, and only declares a pitch **locked** once several consecutive
frames agree within a small cents tolerance.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from .notes import DEFAULT_A4, freq_to_midi, midi_to_freq
from .pitch import PitchResult


@dataclass
class StableState:
    voiced: bool
    locked: bool
    freq: float
    raw_freq: float
    confidence: float
    rms: float
    clipped: bool
    stable_count: int


class StabilityTracker:
    def __init__(
        self,
        a4: float = DEFAULT_A4,
        lock_frames: int = 4,
        tolerance_cents: float = 6.0,
        window: int = 8,
        release_frames: int = 3,
    ) -> None:
        self.a4 = a4
        self.lock_frames = lock_frames
        self.tolerance_cents = tolerance_cents
        self.window = window
        self.release_frames = release_frames
        self._semitones: deque = deque(maxlen=window)
        self._silence = 0
        self._last_locked_freq = 0.0

    def reset(self) -> None:
        self._semitones.clear()
        self._silence = 0
        self._last_locked_freq = 0.0

    def update(self, result: PitchResult) -> StableState:
        if not result.voiced or result.freq <= 0:
            self._silence += 1
            if self._silence >= self.release_frames:
                self._semitones.clear()
                self._last_locked_freq = 0.0
            return StableState(
                voiced=False,
                locked=False,
                freq=self._last_locked_freq,
                raw_freq=0.0,
                confidence=result.confidence,
                rms=result.rms,
                clipped=result.clipped,
                stable_count=0,
            )

        self._silence = 0
        semitone = freq_to_midi(result.freq, self.a4)
        self._semitones.append(semitone)
        median = float(np.median(list(self._semitones)))
        differences = np.abs(np.asarray(self._semitones) - median) * 100.0
        stable_count = int(np.sum(differences <= self.tolerance_cents))
        locked = stable_count >= self.lock_frames and len(self._semitones) >= self.lock_frames

        smoothed = midi_to_freq(median, self.a4)
        if locked:
            self._last_locked_freq = smoothed

        return StableState(
            voiced=True,
            locked=locked,
            freq=smoothed,
            raw_freq=result.freq,
            confidence=result.confidence,
            rms=result.rms,
            clipped=result.clipped,
            stable_count=stable_count,
        )
