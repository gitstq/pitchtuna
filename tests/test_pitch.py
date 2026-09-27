import unittest

import numpy as np

from pitchtuna.generator import synth_note
from pitchtuna.notes import cents_between, note_to_freq
from pitchtuna.pitch import detect_pitch, is_clipped, rms_level

SR = 16000
FS = 8192


def frames_for(freq, seconds=1.2):
    samples = synth_note(freq, SR, seconds)
    return [
        samples[a : a + FS]
        for a in range(0, len(samples) - FS + 1, FS // 2)
    ]


GUITAR = ["E2", "A2", "D3", "G3", "B3", "E4"]


class TestPitch(unittest.TestCase):
    def test_guitar_range_accuracy(self):
        for note in GUITAR:
            target = note_to_freq(note)
            for frame in frames_for(target):
                result = detect_pitch(frame, SR)
                self.assertTrue(result.voiced, msg=f"no pitch for {note}")
                err = abs(cents_between(result.freq, target))
                self.assertLessEqual(err, 3.0, msg=f"{note}: {err:.2f} cents")
                self.assertGreater(result.confidence, 0.7)

    def test_silence_not_voiced(self):
        frame = np.zeros(FS, dtype=np.float32)
        result = detect_pitch(frame, SR)
        self.assertFalse(result.voiced)
        self.assertEqual(result.freq, 0.0)

    def test_noise_low_confidence(self):
        rng = np.random.default_rng(1)
        frame = rng.standard_normal(FS).astype(np.float32) * 0.3
        result = detect_pitch(frame, SR)
        self.assertFalse(result.voiced)
        self.assertLess(result.confidence, 0.6)

    def test_rms_level(self):
        self.assertAlmostEqual(rms_level(np.full(1000, 0.5)), 0.5, places=5)
        self.assertAlmostEqual(rms_level(np.zeros(10)), 0.0)

    def test_clipping(self):
        self.assertTrue(is_clipped(np.ones(10)))
        self.assertFalse(is_clipped(np.full(10, 0.5)))
        result = detect_pitch(np.ones(FS, dtype=np.float32), SR)
        self.assertTrue(result.clipped)

    def test_candidates_recorded(self):
        frame = frames_for(note_to_freq("A4"))[0]
        result = detect_pitch(frame, SR)
        self.assertIn("yin", result.candidates)
        self.assertTrue(len(result.candidates) >= 2)


if __name__ == "__main__":
    unittest.main()
