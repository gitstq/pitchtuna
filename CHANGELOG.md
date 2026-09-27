# Changelog

All notable changes to **PitchTuna** are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-27

### Added
- High-precision pitch engine based on the **YIN** algorithm with parabolic
  (sub-sample) interpolation; measured accuracy within **±1 cent** on the full
  guitar and ukulele ranges on synthetic reference signals.
- Multi-method analysis pipeline: autocorrelation, cumulative mean normalized
  difference (YIN) and harmonic product spectrum (HPS), fused into a single
  frequency estimate with a confidence score.
- Instrument presets and tuning tables: chromatic, acoustic/electric guitar,
  4/5/6-string bass, soprano/concert/tenor ukulele (high- and low-G), violin,
  mandolin and banjo.
- Configurable concert pitch (`--a4`, e.g. 440 / 442 / 432 Hz), down-tuning
  offsets (`--tune-down`) and capo offset (`--capo`).
- Live microphone input via the optional `sounddevice` backend, with automatic
  device listing (`--list-devices`).
- Offline analysis of WAV/PCM files (`--file`) and raw PCM on standard input,
  using only the Python standard library + NumPy.
- Built-in reference-tone generator (`--make-tones`) so users without an
  instrument or microphone can verify and demo the tuner end to end.
- Real-time terminal UI (curses) with note name, cents deviation bar, input
  level meter, target-string highlighting, lock indicator and tuning history.
- One-shot (`--once`), machine-readable (`--json`) and graphical (`--dial`,
  optional pygame) output modes.
- Stability tracker requiring several consistent frames before "locking",
  plus RMS noise gate, clipping detection and harmonic confidence gating.
- Cross-platform launchers: `run.sh`, `run.bat`, `run.command`, plus a
  `Makefile` and an editable-install console script (`pitchtuna`).
- Trilingual documentation: Simplified Chinese, Traditional Chinese and
  English, with clickable language switching.

[1.0.0]: https://github.com/gitstq/pitchtuna/releases/tag/v1.0.0
