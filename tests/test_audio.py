import os
import tempfile
import unittest
import wave

import numpy as np

from pitchtuna.audio import (
    read_raw_pcm,
    read_wav,
    resample_linear,
)
from pitchtuna.generator import synth_note, write_wav


class TestAudio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_wav_roundtrip(self):
        path = os.path.join(self.tmp, "tone.wav")
        samples = synth_note(440.0, 16000, 1.0)
        write_wav(path, samples, 16000)
        loaded, sr = read_wav(path)
        self.assertEqual(sr, 16000)
        self.assertAlmostEqual(len(loaded), len(samples), delta=200)
        self.assertLessEqual(np.max(np.abs(loaded)), 1.0)

    def test_resample_halves(self):
        x = np.arange(16000, dtype=np.float32) / 16000.0
        y = resample_linear(x, 16000, 8000)
        self.assertAlmostEqual(len(y), 8000, delta=2)

    def test_resample_identity(self):
        x = np.linspace(-1, 1, 1000).astype(np.float32)
        y = resample_linear(x, 16000, 16000)
        np.testing.assert_array_equal(x, y)

    def test_raw_pcm(self):
        values = np.array([0, 16384, -16384, 32767], dtype="<i2")
        loaded = read_raw_pcm(values.tobytes())
        self.assertEqual(len(loaded), 4)
        self.assertAlmostEqual(loaded[1], 0.5, places=2)
        self.assertLess(loaded[2], 0)

    def test_stereo_averaged(self):
        path = os.path.join(self.tmp, "stereo.wav")
        mono = (synth_note(220.0, 8000, 0.5) * 32767).astype("<i2")
        stereo = np.repeat(mono.reshape(-1, 1), 2, axis=1)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(stereo.tobytes())
        loaded, sr = read_wav(path)
        self.assertEqual(sr, 8000)
        self.assertEqual(len(loaded), len(mono))
        self.assertAlmostEqual(float(np.max(np.abs(loaded))), float(np.max(np.abs(mono / 32768))), places=2)


if __name__ == "__main__":
    unittest.main()
