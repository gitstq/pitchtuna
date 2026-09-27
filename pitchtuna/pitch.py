"""Pitch detection engine.

Three complementary estimators run on every frame and are fused:

* **YIN** — cumulative mean normalized difference with parabolic
  interpolation; excellent time resolution and cents accuracy (primary).
* **Autocorrelation** — FFT-based periodicity; a robust independent check.
* **HPS** (harmonic product spectrum) — confirms a harmonic (musical) source
  and helps reject noise, tolerating octave relations.

The engine is deliberately dependency-light: it only needs NumPy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np


@dataclass
class PitchResult:
    """Output of analyzing a single frame."""

    freq: float = 0.0
    confidence: float = 0.0
    clarity: float = 0.0
    rms: float = 0.0
    clipped: bool = False
    voiced: bool = False
    candidates: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Level / health
# ---------------------------------------------------------------------------
def rms_level(frame: np.ndarray) -> float:
    return float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))


def is_clipped(frame: np.ndarray) -> bool:
    return bool(np.max(np.abs(frame)) >= 0.999)


# ---------------------------------------------------------------------------
# Autocorrelation via FFT (linear, no circular wrap)
# ---------------------------------------------------------------------------
def _autocorrelation(frame: np.ndarray) -> np.ndarray:
    n = len(frame)
    size = 1 << int(np.ceil(np.log2(2 * n)))
    spectrum = np.fft.fft(frame, size)
    corr = np.fft.ifft(spectrum * np.conj(spectrum)).real
    return corr[:n]


def _parabolic(array: np.ndarray, idx: int) -> float:
    """Sub-sample peak location around integer index ``idx``."""
    if idx <= 0 or idx >= len(array) - 1:
        return float(idx)
    a, b, c = array[idx - 1], array[idx], array[idx + 1]
    denom = a - 2 * b + c
    if denom == 0:
        return float(idx)
    return float(idx) + 0.5 * (a - c) / denom


# ---------------------------------------------------------------------------
# YIN
# ---------------------------------------------------------------------------
def _difference_function(frame: np.ndarray) -> np.ndarray:
    """YIN difference d(tau), computed from FFT autocorrelation."""
    n = len(frame)
    corr = _autocorrelation(frame)
    energy = np.concatenate(([0.0], np.cumsum(frame.astype(np.float64) ** 2)))
    total = energy[-1]
    tau = np.arange(n)
    first = energy[n - tau]          # energy of the first n-tau samples
    second = total - energy[tau]     # energy of samples from tau to the end
    diff = first + second - 2.0 * corr
    diff[0] = 0.0
    return diff


def yin(
    frame: np.ndarray,
    sr: int,
    fmin: float,
    fmax: float,
    threshold: float = 0.15,
):
    """Return ``(freq, clarity)`` using YIN, or ``(0.0, 0.0)``."""
    tau_min = max(2, int(sr / fmax))
    tau_max = min(int(sr / fmin), len(frame) // 2)
    if tau_max <= tau_min + 2:
        return 0.0, 0.0

    diff = _difference_function(frame)
    cmnd = np.ones(len(frame))
    running = np.cumsum(diff[1:])
    taus = np.arange(1, len(frame))
    nonzero = running > 0
    cmnd[1:][nonzero] = diff[1:][nonzero] * taus[nonzero] / running[nonzero]

    tau = tau_min
    found = False
    while tau < tau_max:
        if cmnd[tau] < threshold:
            while tau + 1 < tau_max and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            found = True
            break
        tau += 1
    if not found:
        tau = tau_min + int(np.argmin(cmnd[tau_min:tau_max]))
        if cmnd[tau] > 0.6:
            return 0.0, 0.0

    tau_star = _parabolic(cmnd, tau)
    freq = sr / tau_star
    clarity = float(np.clip(1.0 - cmnd[tau], 0.0, 1.0))
    return float(freq), clarity


# ---------------------------------------------------------------------------
# Plain autocorrelation pitch
# ---------------------------------------------------------------------------
def autocorrelation_pitch(
    frame: np.ndarray, sr: int, fmin: float, fmax: float
) -> float:
    corr = _autocorrelation(frame)
    if corr[0] <= 0:
        return 0.0
    norm = corr / corr[0]
    tau_min = max(2, int(sr / fmax))
    tau_max = min(int(sr / fmin), len(frame) // 2)
    if tau_max <= tau_min:
        return 0.0
    region = norm[tau_min:tau_max]
    idx = int(np.argmax(region)) + tau_min
    if norm[idx] < 0.2:
        return 0.0
    tau_star = _parabolic(norm, idx)
    return float(sr / tau_star)


# ---------------------------------------------------------------------------
# Harmonic product spectrum
# ---------------------------------------------------------------------------
def hps_pitch(frame: np.ndarray, sr: int, fmin: float, fmax: float) -> float:
    windowed = frame * np.hanning(len(frame))
    magnitude = np.abs(np.fft.rfft(windowed))
    if len(magnitude) < 8:
        return 0.0
    product = magnitude.copy()
    for harmonic in range(2, 6):
        step = harmonic
        usable = len(magnitude) // step
        if usable < 4:
            break
        product[:usable] *= magnitude[::step][:usable] + 1e-12
    bin_min = max(1, int(fmin * len(frame) / sr))
    bin_max = min(len(product) - 1, max(bin_min + 1, int(fmax * len(frame) / sr)))
    if bin_max <= bin_min:
        return 0.0
    peak = int(np.argmax(product[bin_min:bin_max])) + bin_min
    if product[peak] <= 0:
        return 0.0
    return float(peak * sr / len(frame))


# ---------------------------------------------------------------------------
# Fusion
# ---------------------------------------------------------------------------
def _octave_equivalent(a: float, b: float, tolerance: float = 0.04) -> bool:
    if a <= 0 or b <= 0:
        return False
    ratio = a / b
    for factor in (0.5, 1.0, 2.0):
        if abs(ratio * factor - 1.0) <= tolerance:
            return True
    return False


def detect_pitch(
    frame: np.ndarray,
    sr: int,
    fmin: float = 50.0,
    fmax: float = 1200.0,
    rms_gate: float = 0.01,
) -> PitchResult:
    """Analyze one frame and return a fused :class:`PitchResult`."""
    frame = np.asarray(frame, dtype=np.float64)
    level = rms_level(frame)
    clipped = is_clipped(frame)
    result = PitchResult(rms=level, clipped=clipped)

    if level < rms_gate:
        result.voiced = False
        return result

    centered = frame - frame.mean()
    peak = np.max(np.abs(centered)) or 1.0
    centered = centered / peak

    f_yin, clarity = yin(centered, sr, fmin, fmax)
    f_ac = autocorrelation_pitch(centered, sr, fmin, fmax)
    f_hps = hps_pitch(centered, sr, fmin, fmax)

    candidates = {"yin": f_yin, "autocorr": f_ac, "hps": f_hps}
    result.candidates = {k: v for k, v in candidates.items() if v > 0}

    primary = f_yin or f_ac or f_hps
    if primary <= 0:
        return result

    others = [v for k, v in result.candidates.items() if v > 0 and v != primary]
    if others:
        agreements = sum(1 for v in others if _octave_equivalent(primary, v))
        agreement = agreements / len(others)
    else:
        agreement = 0.5
    confidence = float(np.clip(0.55 * clarity + 0.45 * agreement, 0.0, 1.0))

    result.freq = primary
    result.clarity = clarity
    result.confidence = confidence
    result.voiced = confidence >= 0.3
    return result
