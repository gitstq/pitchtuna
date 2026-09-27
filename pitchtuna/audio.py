"""Audio input backends and decoders.

* :class:`SoundDeviceBackend` — live microphone input (optional dependency
  ``sounddevice``; PortAudio).
* :func:`read_wav` / :class:`WavFileBackend` — offline WAV analysis using
  only the standard library plus NumPy.
* :func:`read_raw_pcm` — raw int16 PCM from standard input or a byte string.

All samples are returned as mono ``float32`` in the range roughly [-1, 1].
"""

from __future__ import annotations

import queue
import wave
from typing import Iterator, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# WAV decoding
# ---------------------------------------------------------------------------
def _decode_pcm(raw: bytes, sampwidth: int) -> np.ndarray:
    if sampwidth == 1:  # 8-bit WAV is unsigned
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        return (data - 128.0) / 128.0
    if sampwidth == 2:
        return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if sampwidth == 3:
        a = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        signed = (
            a[:, 0]
            | (a[:, 1] << 8)
            | (a[:, 2] << 16)
        )
        signed = np.where(signed & 0x800000, signed - 0x1000000, signed)
        return signed.astype(np.float32) / 8388608.0
    if sampwidth == 4:
        return np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    raise ValueError(f"Unsupported sample width: {sampwidth} bytes")


def read_wav(path: str) -> Tuple[np.ndarray, int]:
    """Read a WAV file as mono float32 and return ``(samples, sample_rate)``."""
    with wave.open(path, "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    samples = _decode_pcm(raw, sampwidth)
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples.astype(np.float32), sr


def resample_linear(data: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr or len(data) == 0:
        return data.astype(np.float32)
    duration = len(data) / src_sr
    target_times = np.arange(int(duration * dst_sr)) / dst_sr
    positions = target_times * src_sr
    i0 = np.floor(positions).astype(np.int64)
    i1 = np.minimum(i0 + 1, len(data) - 1)
    fraction = (positions - i0).astype(np.float32)
    return (data[i0] * (1.0 - fraction) + data[i1] * fraction).astype(np.float32)


class WavFileBackend:
    """Yield fixed-size frames from a WAV file, resampled to ``sample_rate``."""

    def __init__(
        self,
        path: str,
        sample_rate: int = 16000,
        frame_size: int = 8192,
        hop: Optional[int] = None,
    ) -> None:
        samples, sr = read_wav(path)
        self.samples = resample_linear(samples, sr, sample_rate)
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.hop = hop or frame_size

    def frames(self) -> Iterator[np.ndarray]:
        if len(self.samples) < self.frame_size:
            padded = np.zeros(self.frame_size, dtype=np.float32)
            padded[: len(self.samples)] = self.samples
            yield padded
            return
        for start in range(0, len(self.samples) - self.frame_size + 1, self.hop):
            yield self.samples[start : start + self.frame_size].copy()


# ---------------------------------------------------------------------------
# Raw PCM
# ---------------------------------------------------------------------------
def read_raw_pcm(data: bytes, sample_rate: int = 16000) -> np.ndarray:
    """Interpret raw little-endian int16 mono bytes as float32 samples."""
    return np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0


# ---------------------------------------------------------------------------
# Live microphone (optional)
# ---------------------------------------------------------------------------
class SoundDeviceBackend:
    """Microphone backend using ``sounddevice`` (PortAudio)."""

    def __init__(
        self,
        sample_rate: int = 16000,
        blocksize: int = 8192,
        device: Optional[str] = None,
    ) -> None:
        try:
            import sounddevice  # noqa: F401
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Live microphone input needs the optional 'sounddevice' package.\n"
                "Install it with:  pip install sounddevice\n"
                "Or use offline analysis:  python -m pitchtuna --file note.wav"
            ) from exc
        self._sd = sounddevice
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.device = device

    def frames(self) -> Iterator[np.ndarray]:  # pragma: no cover - needs hardware
        q: "queue.Queue[np.ndarray]" = queue.Queue()

        def callback(indata, frames, time_info, status):  # noqa: A002
            if status:
                pass
            q.put(indata[:, 0].copy())

        with self._sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.blocksize,
            channels=1,
            dtype="float32",
            device=self.device,
            callback=callback,
        ):
            while True:
                yield q.get()


def list_input_devices() -> List[dict]:  # pragma: no cover - needs hardware
    try:
        import sounddevice as sd
    except Exception as exc:
        raise RuntimeError(
            "Listing devices needs 'sounddevice': pip install sounddevice"
        ) from exc
    devices = sd.query_devices()
    return [
        {"index": i, "name": d["name"], "channels": d["max_input_channels"]}
        for i, d in enumerate(devices)
        if d["max_input_channels"] > 0
    ]
