import unittest

from pitchtuna.instruments import (
    build_tuning,
    get_instrument,
    list_instruments,
)
from pitchtuna.notes import note_to_freq


class TestInstruments(unittest.TestCase):
    def test_registry(self):
        keys = {i.key for i in list_instruments()}
        for expected in ("chromatic", "guitar", "bass4", "ukulele", "violin"):
            self.assertIn(expected, keys)

    def test_guitar_frequencies(self):
        tuning = build_tuning("guitar")
        expected = ["E2", "A2", "D3", "G3", "B3", "E4"]
        self.assertEqual([rs.note for rs in tuning.strings], expected)
        for rs, note in zip(tuning.strings, expected):
            self.assertAlmostEqual(rs.freq, note_to_freq(note), places=4)

    def test_capo(self):
        base = build_tuning("guitar")
        capo = build_tuning("guitar", capo=2)
        for a, b in zip(base.strings, capo.strings):
            self.assertEqual(b.midi, a.midi + 2)
            self.assertGreater(b.freq, a.freq)

    def test_tune_down(self):
        standard = build_tuning("guitar")
        e_flat = build_tuning("guitar", tune_down=1)
        for a, b in zip(standard.strings, e_flat.strings):
            self.assertEqual(b.midi, a.midi - 1)

    def test_a4(self):
        t440 = build_tuning("guitar", a4=440)
        t442 = build_tuning("guitar", a4=442)
        self.assertGreater(t442.strings[0].freq, t440.strings[0].freq)

    def test_nearest_string(self):
        tuning = build_tuning("guitar")
        rs, c = tuning.nearest(note_to_freq("B3"))
        self.assertEqual(rs.note, "B3")
        self.assertAlmostEqual(c, 0.0, places=2)
        rs2, c2 = tuning.nearest(note_to_freq("B3") * 1.01)
        self.assertEqual(rs2.note, "B3")
        self.assertGreater(c2, 0)

    def test_chromatic_has_no_strings(self):
        tuning = build_tuning("chromatic")
        self.assertTrue(tuning.chromatic)
        self.assertIsNone(tuning.nearest(440.0))

    def test_unknown_instrument(self):
        with self.assertRaises(KeyError):
            get_instrument("does-not-exist")


if __name__ == "__main__":
    unittest.main()
