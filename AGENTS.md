# Maintaining this repository

- `SKILL.md` is the agent-facing contract; `scripts/scan_public.py` is the scanner it describes; README is for
  people. Change the scanner, its tests and the Resources section of `SKILL.md` together.
- Before committing: `python -B -m unittest discover -s tests -v`, then scan this repo with the scanner
  itself, with your private deny list loaded. Both must pass.
- Fake values planted in tests carry a `public-scan: allow` comment; real values never appear anywhere.
- Commit small, one change per commit, with a message that says what changed.
- No dependencies beyond the Python standard library.
