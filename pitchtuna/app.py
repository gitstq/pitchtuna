"""Application controller: wires audio backends, the pitch engine and the UI.

One function per run mode (live curses/dial, file analysis, one-shot, smoke,
tone generation, listings and conversions); :func:`run` dispatches based on
the parsed CLI arguments and returns a process exit code.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from . import audio
from .generator import make_instrument_tones, synth_note
from .instruments import (
    Tuning,
    build_tuning,
    list_instruments,
)
from .notes import (
    DEFAULT_A4,
    freq_to_note,
    note_to_freq,
    note_to_midi,
)
from .pitch import detect_pitch
from .stability import StabilityTracker
from .ui.table import Evaluation, evaluate, render_block, render_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _tuning(args, key: Optional[str] = None) -> Tuning:
    return build_tuning(
        key or args.instrument,
        a4=args.a4,
        capo=args.capo,
        tune_down=args.tune_down,
    )


def _analyze_frames(frames, sample_rate: int, a4: float):
    tracker = StabilityTracker(a4)
    states = []
    for frame in frames:
        result = detect_pitch(frame, sample_rate, rms_gate=0.01)
        state = tracker.update(result)
        states.append(state)
    return states


def _best_state(states):
    voiced = [s for s in states if s.voiced]
    if not voiced:
        return states[-1] if states else None
    locked = [s for s in voiced if s.locked]
    pool = locked or voiced
    return max(pool, key=lambda s: s.confidence)


# ---------------------------------------------------------------------------
# Live microphone
# ---------------------------------------------------------------------------
def run_live(args) -> int:
    from .audio import SoundDeviceBackend

    if args.dial:
        from .ui.dial import run_dial

        tuning = _tuning(args)
        backend = SoundDeviceBackend(args.sample_rate, args.frame_size, args.device)
        run_dial(backend.frames(), args.sample_rate, tuning, args.a4)
        return 0

    from .ui.tui import CursesUI

    keys = [instrument.key for instrument in list_instruments()]
    index = keys.index(args.instrument) if args.instrument in keys else 0
    tuning = _tuning(args, keys[index])
    backend = SoundDeviceBackend(args.sample_rate, args.frame_size, args.device)
    tracker = StabilityTracker(args.a4)

    with CursesUI() as ui:
        for frame in backend.frames():
            result = detect_pitch(frame, args.sample_rate, rms_gate=0.01)
            state = tracker.update(result)
            ev = evaluate(state, tuning, args.a4, args.in_tune_cents)
            ui.draw(ev, tuning, args.a4)
            key = ui.poll_key()
            if key in (ord("q"), ord("Q")):
                break
            if key in (ord("c"), ord("C")):
                step = 1 if key == ord("c") else -1
                index = (index + step) % len(keys)
                tuning = _tuning(args, keys[index])
                tracker = StabilityTracker(args.a4)
    return 0


def run_once(args) -> int:
    from .audio import SoundDeviceBackend

    tuning = _tuning(args)
    backend = SoundDeviceBackend(args.sample_rate, args.frame_size, args.device)
    frames = []
    iterator = backend.frames()
    for _ in range(4):
        frames.append(next(iterator))
    states = _analyze_frames(frames, args.sample_rate, args.a4)
    state = _best_state(states)
    ev = evaluate(state, tuning, args.a4, args.in_tune_cents)
    if args.json:
        import json as _json

        print(_json.dumps(render_json(ev, tuning, args.a4), ensure_ascii=False, indent=2))
    else:
        print(render_block(ev, tuning, args.a4))
    return 0


# ---------------------------------------------------------------------------
# Offline file
# ---------------------------------------------------------------------------
def run_file(args) -> int:
    backend = audio.WavFileBackend(
        args.file,
        sample_rate=args.sample_rate,
        frame_size=args.frame_size,
        hop=args.frame_size // 2,
    )
    states = _analyze_frames(backend.frames(), args.sample_rate, args.a4)
    state = _best_state(states)
    tuning = _tuning(args)
    ev = evaluate(state, tuning, args.a4, args.in_tune_cents)

    if args.json:
        import json as _json

        payload = render_json(ev, tuning, args.a4)
        payload["file"] = args.file
        payload["frames_analyzed"] = len(states)
        distinct = sorted(
            {
                freq_to_note(s.freq, args.a4).name
                for s in states
                if s.voiced
            }
        )
        payload["detected_notes"] = distinct
        print(_json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_block(ev, tuning, args.a4))
        voiced_notes = sorted(
            {freq_to_note(s.freq, args.a4).name for s in states if s.voiced}
        )
        if voiced_notes:
            print(f"\n🎼 Notes detected across the file: {' '.join(voiced_notes)}")
    return 0


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def run_smoke(args) -> int:
    tuning = build_tuning("guitar", a4=440.0)
    print("== PitchTuna smoke test ==")
    all_ok = True
    for rs in tuning.strings:
        samples = synth_note(rs.freq, args.sample_rate, seconds=1.2)
        frames = []
        for start in range(0, len(samples) - args.frame_size + 1, args.frame_size // 2):
            frames.append(samples[start : start + args.frame_size])
        states = _analyze_frames(frames, args.sample_rate, 440.0)
        state = _best_state(states)
        ev = evaluate(state, tuning, 440.0, args.in_tune_cents)
        good = abs(ev.cents) <= 5.0
        all_ok &= good
        print(
            f"  {rs.note:>3} -> {ev.freq:8.2f} Hz  {ev.cents:+6.2f} cents  "
            f"conf {ev.confidence:.2f}  {'OK' if good else 'FAIL'}"
        )

    # Graphical dial screenshot (optional dependency)
    shot = os.path.join("docs", "screenshots", "dial.png")
    try:
        from .ui.dial import run_dial

        target = next(rs for rs in tuning.strings if rs.note == "B3")
        samples = synth_note(target.freq, args.sample_rate, seconds=2.0)
        frames = [
            samples[start : start + args.frame_size]
            for start in range(0, len(samples) - args.frame_size + 1, args.frame_size // 2)
        ]
        os.makedirs(os.path.dirname(shot), exist_ok=True)
        run_dial(frames, args.sample_rate, tuning, 440.0, max_frames=len(frames),
                 save_path=shot)
        print(f"  graphical dial rendered -> {shot}")
    except Exception as exc:  # graphical extras are optional
        print(f"  dial screenshot skipped ({exc.__class__.__name__})")

    print("SMOKE RESULT:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


# ---------------------------------------------------------------------------
# Tone generation / listings / conversions
# ---------------------------------------------------------------------------
def run_make_tones(args) -> int:
    tuning = _tuning(args)
    paths = make_instrument_tones(tuning, args.make_tones, args.sample_rate)
    print(f"🎵 Wrote {len(paths)} reference tone(s) to {args.make_tones}:")
    for path in paths:
        print("  ", path)
    return 0


def run_list_instruments(_args) -> int:
    print("Available instrument presets:")
    for instrument in list_instruments():
        notes = " ".join(spec.note for spec in instrument.strings) or "(all notes)"
        print(f"  {instrument.emoji} {instrument.key:14} {instrument.name}")
        print(f"      {notes}")
        if instrument.description:
            print(f"      {instrument.description}")
    return 0


def run_list_devices(_args) -> int:
    devices = audio.list_input_devices()
    print("Input devices:")
    for device in devices:
        print(f"  [{device['index']}] {device['name']}  ({device['channels']} in)")
    return 0


def run_convert(args) -> int:
    if args.note:
        midi = note_to_midi(args.note)
        freq = note_to_freq(args.note, args.a4)
        print(f"🎵 {args.note}: MIDI {midi}, {freq:.3f} Hz (A4={args.a4:g})")
    if args.freq:
        info = freq_to_note(args.freq, args.a4)
        print(
            f"📻 {args.freq:.3f} Hz -> {info.name} "
            f"(MIDI {info.midi}, {info.cents:+.2f} cents to nearest note)"
        )
    return 0


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
def run(args) -> int:
    if args.list_instruments:
        return run_list_instruments(args)
    if args.list_devices:
        return run_list_devices(args)
    if args.smoke_test:
        return run_smoke(args)
    if args.make_tones:
        return run_make_tones(args)
    if args.note or args.freq:
        return run_convert(args)
    if args.file:
        return run_file(args)
    if args.once:
        return run_once(args)
    return run_live(args)
