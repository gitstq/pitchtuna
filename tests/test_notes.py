import math
import unittest

from pitchtuna.notes import (
    A4_MIDI,
    cents_between,
    freq_to_midi,
    freq_to_note,
    midi_to_freq,
    midi_to_note,
    note_to_freq,
    note_to_midi,
)


class TestNotes(unittest.TestCase):
    def test_well_known_midi(self):
        self.assertEqual(note_to_midi("A4"), 69)
        self.assertEqual(note_to_midi("C4"), 60)
        self.assertEqual(note_to_midi("E2"), 40)
        self.assertEqual(note_to_midi("C-1"), 0)

    def test_accidentals(self):
        self.assertEqual(note_to_midi("C#4"), 61)
        self.assertEqual(note_to_midi("Db4"), 61)
        self.assertEqual(note_to_midi("Eb2"), note_to_midi("D#2"))
        self.assertEqual(note_to_midi("Cx4"), note_to_midi("D4"))
        self.assertEqual(note_to_midi("Cbb4"), note_to_midi("Bb3"))
        self.assertEqual(note_to_midi("A\u266f4"), note_to_midi("A#4"))

    def test_midi_to_note(self):
        self.assertEqual(midi_to_note(69), "A4")
        self.assertEqual(midi_to_note(61, prefer_flats=True), "Db4")

    def test_frequencies(self):
        self.assertAlmostEqual(midi_to_freq(A4_MIDI), 440.0)
        self.assertAlmostEqual(note_to_freq("A3"), 220.0)
        self.assertAlmostEqual(note_to_freq("A5"), 880.0)
        self.assertAlmostEqual(freq_to_midi(440.0), 69.0)

    def test_a4_override(self):
        self.assertAlmostEqual(note_to_freq("A4", a4=442.0), 442.0)

    def test_freq_to_note(self):
        info = freq_to_note(440.0)
        self.assertEqual(info.name, "A4")
        self.assertAlmostEqual(info.cents, 0.0, places=3)
        sharp = freq_to_note(445.0)
        self.assertEqual(sharp.pitch_class, "A")
        self.assertGreater(sharp.cents, 0)

    def test_cents_between(self):
        self.assertAlmostEqual(cents_between(880.0, 440.0), 1200.0)
        self.assertAlmostEqual(cents_between(220.0, 440.0), -1200.0)
        self.assertAlmostEqual(cents_between(440.0, 440.0), 0.0)

    def test_invalid_note(self):
        with self.assertRaises(ValueError):
            note_to_midi("Z4")

    def test_invalid_freq(self):
        with self.assertRaises(ValueError):
            freq_to_midi(0)


if __name__ == "__main__":
    unittest.main()
