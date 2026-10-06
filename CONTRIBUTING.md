# Contributing to Giorgio

Thanks for looking. Giorgio is an open design: anyone may fork it, study it, build on it and propose changes.

## How to propose a change
1. **Open an issue first** for anything bigger than a typo: describe the problem or idea, and which folder it touches
   (`amr/`, `cad/`, `electrical/`, `giorgio_os/`, `rl_*`, simulation, `render/`).
2. **Fork** the repository, create a branch (`feature/<short-name>` or `fix/<short-name>`), make the change.
3. **Run the checks** of the area you touched and paste the summary in the pull request. `make check` runs the fast ones
   (the same as CI). `make help` lists them all. Environments: `make setup` (sim), `cad/requirements.txt` (CAD),
   `requirements-train.txt` (GPU training).
   - own base: `make amr-check` (PyYAML + numpy), and `make amr-cad` in the CAD env if you changed geometry
   - superstructure CAD: `make cad-validate`
   - simulation: `PYTHONPATH=. python verifiche/aggancio.py 1`, `PYTHONPATH=. python verifiche/urti.py logistica`,
     `PYTHONPATH=. python stability_test.py amr quick`
   - software: `make test` (GIORGIO-OS; 4 sim-skill tests are known to fail since the rev B base, see the issues)
   - BOM: if you changed `amr/bom_amr.csv` or `docs/bom.csv`, run `python scripts/bom_overview.py`
4. **Open a pull request** against `master` with: what changed, why, and the check results.

## Rules for technical data
- Every purchased-part value must come from an **official manufacturer document** (datasheet, manual, certificate), with
  the URL and page, and a tag: SOURCED / SECONDARY / ESTIMATE / ASSUMED. Do not present an estimate as a fact.
- Safety functions stay **deterministic and certified** (scanners, safety controller, safety drives). No machine-learning
  model may perform a safety function (EU Machinery Regulation 2023/1230, Annex I).
- Do not commit manufacturer PDFs (copyright); link them instead.

## Licences of contributions
By contributing you agree that your contribution is licensed like the files you change: software Apache-2.0,
hardware/CAD CERN-OHL-S-2.0, documents and media CC BY 4.0.

## Conduct
Be kind and specific. Critique designs, not people. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## New here?
- Start with an issue labelled [good first issue](https://github.com/VenetoStato/giorgio/labels/good%20first%20issue).
- [docs/CUSTOMIZE.md](docs/CUSTOMIZE.md) shows where every knob lives.
- [docs/GLOSSARY.md](docs/GLOSSARY.md) translates the Italian file and variable names that remain in the code.
- English is preferred in code and docs; Italian is fine in issues and discussions.
