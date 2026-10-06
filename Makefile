# Giorgio task list. `make help` lists everything.
# Override the interpreters with env vars: PYTHON (sim/checks), CADPY (CadQuery env), BLENDER (Blender 4.5).
PYTHON  ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
CADPY   ?= $(if $(wildcard cad/.env/bin/python),cad/.env/bin/python,python3)
BLENDER ?= blender
export MUJOCO_GL ?= egl
export PYTHONPATH := $(CURDIR)

.PHONY: help setup fetch sim sim-video coffee console test check syntax amr-check electrical amr-cad cad-validate render-amr

help:            ## list the tasks
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-13s %s\n", $$1, $$2}'

setup:           ## create .venv, install requirements, fetch third_party (one command)
	bash scripts/setup.sh

fetch:           ## (re)fetch the third-party robot models at the pinned commits
	bash scripts/fetch_third_party.sh

sim:             ## GUI simulation: logistics mission (needs a display)
	$(PYTHON) giorgio_v5.py

sim-video:       ## headless: 40 s of the logistics mission to video/sim.mp4
	mkdir -p video && $(PYTHON) giorgio_v5.py --seconds 40 --video video/sim.mp4

coffee:          ## GUI simulation: "make me a coffee and bring it to Marco"
	$(PYTHON) giorgio_v5.py --agent "1:Giorgio, fammi un caffe e portalo a Marco" --seconds 100

console:         ## GIORGIO-OS operator console + simulated robot at http://127.0.0.1:8080
	$(PYTHON) -m giorgio_os.sim_server

test:            ## GIORGIO-OS tests (headless, ~40 s)
	cd giorgio_os && $(abspath $(PYTHON)) -m pytest -q

check: syntax amr-check electrical  ## fast checks, the same as CI (seconds; needs only PyYAML + numpy)

syntax:          ## byte-compile every tracked Python file
	git ls-files -z '*.py' | xargs -0 $(PYTHON) -m py_compile

amr-check:       ## AMR electrical/safety checks + engineering calculations
	$(PYTHON) amr/electrical/check_amr.py
	cd amr && $(abspath $(PYTHON)) amr_calc.py > /dev/null && echo "amr_calc: OK, see amr/CALC.md"

electrical:      ## superstructure electrical checks (2 FAILs are documented and kept on purpose)
	-$(PYTHON) electrical/calc.py

cad-validate:    ## superstructure CAD build + checks + exports (CadQuery env, ~2.5 min)
	cd cad && $(abspath $(CADPY)) validate.py

amr-cad:         ## AMR CAD build + keep-out checks + fit of the superstructure (CadQuery env; run cad-validate first)
	cd amr && $(abspath $(CADPY)) amr_cad.py && $(abspath $(CADPY)) integrate.py && $(abspath $(CADPY)) amr_calc.py

render-amr:      ## Blender render of the AMR hero shot -> amr/renders/amr_hero.png
	$(BLENDER) -b -P amr/render_amr.py -- --view hero --out amr/renders/amr_hero.png
