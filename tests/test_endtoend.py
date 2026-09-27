import tempfile
import unittest

from pitchtuna.app import _analyze_frames, _best_state
from pitchtuna.audio import WavFileBackend
from pitchtuna.generator import make_instrument_tones
from pitchtuna.instruments import build_tuning
from pitchtuna.ui.table import evaluate


class TestEndToEnd(unittest.TestCase):
    def test_generated_guitar_tones_are_recognized(self):
        tmp = tempfile.mkdtemp()
        tuning = build_tuning("guitar", a4=440.0)
        paths = make_instrument_tones(tuning, tmp, sample_rate=16000, seconds=1.5)

        self.assertEqual(len(paths), len(tuning.strings))
        for path, rs in zip(paths, tuning.strings):
            backend = WavFileBackend(path, sample_rate=16000, frame_size=8192, hop=4096)
            states = _analyze_frames(backend.frames(), 16000, 440.0)
            state = _best_state(states)
            ev = evaluate(state, tuning, 440.0)
            self.assertTrue(ev.voiced, msg=f"no pitch for {rs.note}")
            self.assertTrue(ev.locked, msg=f"did not lock for {rs.note}")
            self.assertLessEqual(abs(ev.cents), 5.0, msg=f"{rs.note} off by {ev.cents}")
            self.assertEqual(ev.target_note, rs.note.replace("E4", "E4"))

    def test_ukulele_preset_end_to_end(self):
        tmp = tempfile.mkdtemp()
        tuning = build_tuning("ukulele", a4=440.0)
        paths = make_instrument_tones(tuning, tmp, 16000, 1.5)
        for path, rs in zip(paths, tuning.strings):
            backend = WavFileBackend(path, 16000, 8192, 4096)
            states = _analyze_frames(backend.frames(), 16000, 440.0)
            ev = evaluate(_best_state(states), tuning, 440.0)
            self.assertTrue(ev.voiced)
            self.assertLessEqual(abs(ev.cents), 5.0)


if __name__ == "__main__":
    unittest.main()
