# Glossary: Italian names in the code

Giorgio started as an Italian side project, so many file names, variables, CLI help texts and comments are still in
Italian. New documents are written in English; renaming the code is a welcome contribution, but please do it in small
pull requests that keep every check passing. Until then, this table should help.

## Files and folders

| Italian | English | Where |
|---|---|---|
| `verifiche/` | checks, verification scripts | top level |
| `aggancio` | docking (coupling to the charging dock) | `verifiche/aggancio.py` |
| `urti` | collisions, impacts | `verifiche/urti.py` |
| `carene`, `gusci` | fairings, shells (the cosmetic covers) | `verifiche/carene.py`, `verifiche/gusci_reali.py`, `shells.py` |
| `gusci_reali` | real (manufacturable) shells | `verifiche/gusci_reali.py` |
| `collari` | collars, rings (shell openings around the arms) | `verifiche/collari.py` |
| `scatole` / `scatola` | boxes / box | `giorgio_scatole.py`, `verifiche/scatole_v14.py` |
| `scatole_forze` | box forces (contact forces on the boxes) | `verifiche/scatole_forze_v14.py` |
| `ricarica` | recharge, charging | `rec_ricarica.py`, `render/ricarica_energia.json` |
| `rec_*` | recording (a pickled simulation run used for renders) | `rec_ricarica.py`, `render/rec_*.pkl` (git-ignored) |
| `smista`, `smistamento` | sort, sorting | `giorgio_sort.py`, `render/v19/s_smista/` |
| `consegna` | hand-over, delivery | `render/v19/c_consegna/` |
| `carico` | loading | `render/v19/l_carico/` |
| `eroga` | brews, dispenses (coffee) | `render/v19/c_eroga/` |
| `bicchiere` | cup | `render/v19/c_bicchiere/` |
| `prende` | picks up | `render/v19/c_prende/` |
| `caffe` | coffee | `render/lab_caffe.json`, `--agent` commands |
| `rifai_*` | redo (re-run a whole pipeline) | `legacy/rifai_*.sh` |
| `crea_edit_vNN` | create the video edit, version NN | `render/crea_edit_v*.py` |
| `finale_vNN` | final cut, version NN | `render/finale_v*.sh` |
| `stills_*` | still images (not Italian, but our folder name for single frames) | `render/stills_v10/` |
| `RIPRENDI_RENDER` | resume the render | `render/RIPRENDI_RENDER.txt` |
| `marchi` | trademarks | `render/marchi_v14.txt` |
| `bom_totale` | total BOM | `render/bom_totale.txt` |
| `diagramma_energia` | energy diagram | `render/diagramma_energia*.py` |
| `cad_anatomia` | CAD anatomy (exploded view animation) | `render/cad_anatomia.py` |
| `card_codice` | code card (title card showing code) | `render/card_codice.py` |
| `edit_prov` | provisional edit | `render/edit_prov.json` |
| `cappelli` | hats | `render/verifica_cappelli.py` |
| `verifica_testi` | check the on-screen texts | `render/verifica_testi.py` |
| `logo_chiaro` | light-background logo | `render/logo/` |
| `mani` | hands | `rl_mani/`, `giorgio_hands.py` docstring |
| `valutazione` | evaluation | `rl_mani/valutazione/`, `rl_openarm/valutazione/` |
| `curva_apprendimento` | learning curve | `rl_mani/curva_apprendimento.png` |
| `politica_*` | policy (trained network weights) | `rl_mani/politica_orca_cubo.pt`, `rl_openarm/politica_openarm_*.pt` |
| `cubo` | cube | `rl_mani/orca_cubo_rl.xml` |
| `grafico` | chart, plot | `rl_mani/grafico.py`, `rl_openarm/grafico*.py` |
| `prima` / `dopo` | before / after (training) | `rl_mani/prima.mp4`, `dopo.mp4` (git-ignored) |
| `traiettoria` | trajectory | `rl_mani/traiettoria_dopo.npz` |
| `valuta_e_video` | evaluate and make a video | `rl_mani/valuta_e_video.py` |
| `modello.pt` | model checkpoint | `rl_*/runs/*/` |
| `alimentazione_e_certificazione` | power supply and certification | `docs/alimentazione_e_certificazione.md` |
| `campagna` | campaign | `kickstarter/campagna_IT.md` |
| `componenti`, `attivita`, `personalizza`, `lungo` | components, activities, customisation, long (full) — the video series names | `render/video_series.py` |

## Words you will meet in variables, arguments and comments

| Italian | English | Typical use |
|---|---|---|
| `braccio` / `braccia` | arm / arms | `braccio_dx` = right arm |
| `dx` / `sx` | right / left (destra / sinistra) | label keys |
| `pinza` | gripper | |
| `dita` | fingers | hand models |
| `presa` | grasp | grasp poses |
| `posa` | pose | |
| `busto` | torso | |
| `testa` / `volto` | head / face | LED face (`render/ledface.py`) |
| `baffi`, `occhi` | moustache, eyes | face drawing |
| `colonna` | column (torso support) | |
| `zaino` | backpack (the coffee module on the back) | `--xray` help text |
| `vassoio` | tray | front buffer tray |
| `flacone` / `flaconi` | bottle(s), flask(s) | kitting objects |
| `banco` | bench, workbench | stations A/B |
| `stazione` | station | |
| `scaffale` | shelf | coffee shelf |
| `macchina` (del caffè) | (coffee) machine | |
| `ruote`, `piroette` | wheels, castors | AMR model |
| `carrello`, `piedini` | cart, levelling feet | historic `base="cart"` option |
| `carica` | charge (battery) | `--soc` help text |
| `sicurezza` | safety | scanner fields |
| `velocita` | speed | |
| `persone` / `passante` | people / passer-by | simulated humans |
| `posteriore` / `anteriore` | rear / front | tray variants |
| `lato` | side (also: cube side length) | |
| `sotto` / `sopra` | below / above | |
| `fotogramma` / `fotogrammi` | frame(s) of video | render scripts |
| `ribaltamento` | tipping over | `stability_test.py` |

## Command-line values and on-screen strings

| Italian | English | Where |
|---|---|---|
| `--agent "1:Giorgio, fammi un caffe e portalo a Marco"` | "at t = 1 s: Giorgio, make me a coffee and bring it to Marco" (format `t:text\|t:text`) | `giorgio_v5.py` |
| `--agent "999:nulla"` | "nothing" (no command; used by the docking check) | `verifiche/aggancio.py` |
| looks `gb`, `eva`, `akira`, `gits`, `blame`, `cyber` | colour schemes (paint/accent/visor), not Italian but named after styles | `LOOKS` in `giorgio_model.py`, `--look` |
| hats `coppola`, `bustina`, `snapback` | Sicilian flat cap, side cap (garrison/barista cap), snapback | `render/hats.py`, `--hat` in `render/blender_render.py` |
| face codes `0 neutro, 1 contento, 2 caffe', 3 stop, 4 pensa, 5 cuori, 6 attento` | neutral, happy, coffee, stop, thinking, hearts, alert | `render/ledface.py` |
| `uso:` | usage: | script docstrings |
