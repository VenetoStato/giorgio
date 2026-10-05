# Contributing to Giorgio

Thanks for looking. Giorgio is an open design: anyone may fork it, study it, build on it and propose changes.

## How to propose a change
1. **Open an issue first** for anything bigger than a typo: describe the problem or idea, and which folder it touches
   (`amr/`, `cad/`, `electrical/`, `giorgio_os/`, `rl_*`, simulation, `render/`).
2. **Fork** the repository, create a branch (`feature/<short-name>` or `fix/<short-name>`), make the change.
3. **Run the checks** of the area you touched and paste the summary in the pull request:
   - own base: `cd amr && ../cad/.env/bin/python amr_cad.py && ../cad/.env/bin/python integrate.py && ../cad/.env/bin/python amr_calc.py`, `python3 electrical/check_amr.py`
   - superstructure CAD: `cd cad && .env/bin/python validate.py`
   - simulation: `verifiche/aggancio.py`, `verifiche/urti.py`, `stability_test.py amr quick`
   - software: `pytest` in `giorgio_os/`
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
Be kind and specific. Critique designs, not people.
