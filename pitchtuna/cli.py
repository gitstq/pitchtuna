"""Command-line interface for PitchTuna."""

from __future__ import annotations

import argparse
from typing import List, Optional

from . import __version__
from .app import run
from .notes import DEFAULT_A4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pitchtuna",
        description=(
            "PitchTuna — a high-precision, multi-instrument tuner in your "
            "terminal. Default: live microphone tuner for guitar."
        ),
        epilog=(
            "Examples:\n"
            "  pitchtuna                         # live guitar tuner\n"
            "  pitchtuna -i ukulele              # live ukulele tuner\n"
            "  pitchtuna --file string.wav       # analyze a recording\n"
            "  pitchtuna --make-tones examples   # generate reference tones\n"
            "  pitchtuna --smoke-test            # headless self-check\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"PitchTuna {__version__}"
    )

    instrument = parser.add_argument_group("instrument / tuning")
    instrument.add_argument(
        "-i",
        "--instrument",
        default="guitar",
        help="instrument preset key (see --list-instruments). Default: guitar",
    )
    instrument.add_argument(
        "--a4",
        type=float,
        default=DEFAULT_A4,
        help="concert pitch A4 frequency in Hz (e.g. 440, 442, 432). Default: 440",
    )
    instrument.add_argument(
        "--capo",
        type=int,
        default=0,
        metavar="FRETS",
        help="capo position; shifts every string up by N semitones. Default: 0",
    )
    instrument.add_argument(
        "--tune-down",
        type=int,
        default=0,
        metavar="SEMITONES",
        help="down-tune all strings by N semitones (e.g. Eb standard = 1). Default: 0",
    )
    instrument.add_argument(
        "--in-tune-cents",
        type=float,
        default=5.0,
        help="cents window considered in tune. Default: 5",
    )

    audio_group = parser.add_argument_group("audio")
    audio_group.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="analysis sample rate in Hz. Default: 16000",
    )
    audio_group.add_argument(
        "--frame-size",
        type=int,
        default=8192,
        help="analysis frame size in samples. Default: 8192",
    )
    audio_group.add_argument(
        "--device",
        default=None,
        help="microphone device index/name for live input (see --list-devices)",
    )

    modes = parser.add_argument_group("run modes")
    modes.add_argument(
        "--file",
        metavar="WAV",
        help="analyze a WAV file offline instead of using the microphone",
    )
    modes.add_argument(
        "--once",
        action="store_true",
        help="capture a few frames, report once and exit",
    )
    modes.add_argument(
        "--json",
        action="store_true",
        help="machine-readable JSON output (with --once or --file)",
    )
    modes.add_argument(
        "--dial",
        action="store_true",
        help="use the optional graphical window instead of the terminal UI",
    )
    modes.add_argument(
        "--smoke-test",
        action="store_true",
        help="headless self-check using synthetic tones; exit 0 on success",
    )
    modes.add_argument(
        "--make-tones",
        metavar="DIR",
        help="generate reference WAV tones for the instrument into DIR",
    )
    modes.add_argument(
        "--list-instruments",
        action="store_true",
        help="list all instrument presets and exit",
    )
    modes.add_argument(
        "--list-devices",
        action="store_true",
        help="list microphone input devices and exit",
    )

    convert = parser.add_argument_group("conversion utilities")
    convert.add_argument("--note", help="convert a note name (e.g. A4) to Hz/MIDI")
    convert.add_argument("--freq", type=float, help="convert a frequency to a note")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        return 130
    except RuntimeError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
