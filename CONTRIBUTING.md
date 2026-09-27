# Contributing to PitchTuna 🎣

First off, thank you for taking the time to contribute! PitchTuna is a small,
friendly project and every bug report, idea, doc fix or pull request genuinely
helps.

## 🐛 Reporting issues

- Use the [issue tracker](https://github.com/gitstq/pitchtuna/issues).
- Search existing issues first to avoid duplicates.
- Please include: your OS, Python version (`python --version`), the command you
  ran, and what you expected vs. what happened.
- For pitch-detection problems, attach a short WAV recording if you can
  (files work great with `pitchtuna --file your.wav --json`).

## 💡 Suggesting features

Open an issue with the tag idea and describe the problem you are trying to
solve, a possible approach, and the instrument(s) it would help tune.

## 🔀 Pull request process

1. Fork the repository and create your branch from `main`.
2. Keep changes focused; one logical change per pull request.
3. Add or update tests for any code you touch, and make sure the suite passes:

   ```bash
   make test
   ```

4. Run the headless smoke check before submitting:

   ```bash
   make smoke
   ```

5. Update docs / `CHANGELOG.md` when relevant.
6. Open the pull request and fill in the template.

## ✍️ Commit message convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) /
Angular style:

```
feat: add 7-string guitar preset
fix: correct low-G ukulele root note
docs: improve Windows installation steps
refactor: split audio backends into modules
test: cover HPS confidence gating
chore: bump numpy pin
```

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`,
`perf`, `build`, `ci`.

## 🎨 Code style

- Target Python 3.9+; prefer the standard library and keep the core dependency
  surface small (NumPy only for the engine).
- Write clear docstrings and comments; public functions should state units
  (Hz, cents, samples, seconds).
- Platform-specific code must degrade gracefully when an optional dependency or
  OS API is unavailable — never crash because `sounddevice`/`pygame` is missing.

## 🌍 Adding a language

You are very welcome to translate the README into another language. Add
`README.<code>.md` and link it from the language switcher at the top of every
README. Please use natural, native-sounding wording rather than literal machine
translation.

## 📄 License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
