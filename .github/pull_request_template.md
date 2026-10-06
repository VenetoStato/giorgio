## What and why

<!-- What does this change, and why? Link the issue it closes, e.g. "Closes #12". -->

## Area

<!-- amr / cad / electrical / simulation / giorgio_os / training (rl_*) / render-video / docs / other -->

## Checks run

<!-- Paste the summary lines of the checks for the area you touched (`make check` runs the fast ones if available). -->

- [ ] Fast checks: `python .github/scripts/check_links.py`, `python amr/electrical/check_amr.py`, `python electrical/calc.py` (or `make check`)
- [ ] Own base (`amr/`): `cd amr && python amr_cad.py && python integrate.py && python amr_calc.py` (CadQuery env, see `cad/README.md`)
- [ ] Superstructure CAD (`cad/`): `cd cad && python validate.py` (CadQuery env)
- [ ] Simulation: `python verifiche/aggancio.py`, `python verifiche/urti.py`, `python stability_test.py amr quick`
- [ ] Software (`giorgio_os/`): `cd giorgio_os && python -m pytest`
- [ ] Not applicable (docs-only change)

## Checklist

- [ ] New or changed technical values cite an official source (URL + page) and carry a tag: SOURCED / SECONDARY / ESTIMATE / ASSUMED
- [ ] No manufacturer PDFs, no secrets or API keys, no files larger than 50 MB (link documents instead)
- [ ] If the geometry changed: generated reports (CHECKS / VALIDATION / CALC) and affected renders were regenerated, or I said why not
- [ ] Safety functions stay deterministic and certified (no ML model in a safety function)
- [ ] I agree that my contribution is licensed like the files it changes: software Apache-2.0, hardware/CAD CERN-OHL-S-2.0, documents and media CC BY 4.0
