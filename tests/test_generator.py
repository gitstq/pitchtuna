import os
import tempfile
import unittest

from pitchtuna.generator import (
    make_instrument_tones,
    synth_note,
    write_wav,
)
from pitchtuna.instruments import build_tuning
from pitchtuna.notes import note_to_freq
from pitchtuna.pitch import detect_pitch


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_synth_length_and_range(self):
        samples = synth_note(440.0, 16000, 1.5)
        self.assertEqual(len(samples), 24000)
        self.assertLessEqual(abs(samples).max(), 1.0)

    def test_written_wav_has_right_pitch(self):
        path = os.path.join(self.tmp, "a4.wav")
        write_wav(path, synth_note(note_to_freq("A4"), 16000, 1.2), 16000)
        from pitchtuna.audio import read_wav

        samples, sr = read_wav(path)
        frame = samples[:8192]
        result = detect_pitch(frame, sr)
        self.assertTrue(result.voiced)
        self.assertAlmostEqual(result.freq, 440.0, delta=1.0)

    def test_make_instrument_tones_count(self):
        tuning = build_tuning("guitar")
        paths = make_instrument_tones(tuning, self.tmp, 16000)
        self.assertEqual(len(paths), len(tuning.strings))
        for path in paths:
            self.assertTrue(os.path.exists(path))
            self.assertTrue(path.endswith(".wav"))


if __name__ == "__main__":
    unittest.main()
