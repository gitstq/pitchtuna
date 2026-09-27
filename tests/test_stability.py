import unittest

import numpy as np

from pitchtuna.generator import synth_note
from pitchtuna.notes import note_to_freq
from pitchtuna.pitch import detect_pitch
from pitchtuna.stability import StabilityTracker

SR = 16000
FS = 8192


def frames_for(freq, count=8):
    samples = synth_note(freq, SR, seconds=3.0)
    frames = [
        samples[a : a + FS]
        for a in range(0, len(samples) - FS + 1, FS // 2)
    ]
    return frames[:count]


class TestStability(unittest.TestCase):
    def test_locks_after_consistent_frames(self):
        tracker = StabilityTracker(440.0, lock_frames=4, tolerance_cents=6.0)
        states = [tracker.update(detect_pitch(f, SR)) for f in frames_for(note_to_freq("A4"))]
        self.assertFalse(states[0].locked)
        self.assertTrue(any(s.locked for s in states))
        locked = next(s for s in states if s.locked)
        self.assertAlmostEqual(locked.freq, note_to_freq("A4"), delta=1.0)

    def test_silence_releases_lock(self):
        tracker = StabilityTracker(440.0)
        for f in frames_for(note_to_freq("A4")):
            tracker.update(detect_pitch(f, SR))
        self.assertTrue(tracker.update(detect_pitch(frames_for(note_to_freq("A4"))[0], SR)).locked)
        for _ in range(5):
            state = tracker.update(detect_pitch(np.zeros(FS, dtype=np.float32), SR))
        self.assertFalse(state.voiced)
        self.assertFalse(state.locked)

    def test_small_detune_still_tracks(self):
        tracker = StabilityTracker(440.0, lock_frames=3, tolerance_cents=8.0)
        target = note_to_freq("A4") * 1.001  # ~1.7 cents sharp
        states = [tracker.update(detect_pitch(f, SR)) for f in frames_for(target)]
        self.assertTrue(any(s.locked for s in states))

    def test_reset(self):
        tracker = StabilityTracker(440.0)
        tracker.update(detect_pitch(frames_for(note_to_freq("A4"))[0], SR))
        tracker.reset()
        state = tracker.update(detect_pitch(np.zeros(FS, dtype=np.float32), SR))
        self.assertFalse(state.voiced)


if __name__ == "__main__":
    unittest.main()
