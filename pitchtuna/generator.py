"""Reference-tone synthesis and WAV writing.

Lets users without an instrument (or a microphone) verify the tuner end to
end, and provides a deterministic signal source for demos and tests. Sounds
are additive (fundamental + decaying harmonics) with a touch of noise, so
there are no bundled audio files and no licensing concerns.
"""

from __future__ import annotations

import os
import wave
from typing import Dict, List

import numpy as np


def synth_note(
    freq: float,
    sample_rate: int = 16000,
    seconds: float = 1.5,
    harmonics: int = 6,
    noise: float = 0.004,
    seed: int = 4,
) -> np.ndarray:
    n = int(sample_rate * seconds)
    t = np.arange(n) / sample_rate
    signal = np.zeros(n)
    for k in range(1, harmonics + 1):
        if freq * k >= sample_rate / 2.0:
            break
        signal += (1.0 / k) * np.sin(2 * np.pi * freq * k * t)
    rng = np.random.default_rng(seed)
    signal += noise * rng.standard_normal(n)
    # Attack / release envelope to avoid edge clicks.
    attack = max(1, int(0.01 * sample_rate))
    release = max(1, int(0.08 * sample_rate))
    env = np.ones(n)
    env[:attack] = np.linspace(0.0, 1.0, attack)
    env[-release:] = np.linspace(1.0, 0.0, release)
    signal *= env
    peak = np.max(np.abs(signal)) or 1.0
    return (signal / peak * 0.85).astype(np.float32)


def write_wav(path: str, samples: np.ndarray, sample_rate: int = 16000) -> None:
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def make_instrument_tones(
    tuning,
    outdir: str,
    sample_rate: int = 16000,
    seconds: float = 1.5,
) -> List[str]:
    """Write one WAV per open string and return the file paths."""
    paths: List[str] = []
    os.makedirs(outdir, exist_ok=True)
    used: Dict[str, int] = {}
    for rs in tuning.strings:
        base = rs.note.replace("#", "s")
        filename = f"{tuning.instrument.key}_{base}.wav"
        if filename in used:
            used[filename] += 1
            filename = f"{tuning.instrument.key}_{base}_{used[filename]}.wav"
        else:
            used[filename] = 0
        path = os.path.join(outdir, filename)
        samples = synth_note(rs.freq, sample_rate, seconds)
        write_wav(path, samples, sample_rate)
        paths.append(path)
    return paths
