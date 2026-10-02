# Giorgio-P — umanoide su base mobile da componenti reali

Simulazione MuJoCo 3.8 (stesso motore del SolverMuJoCo di Newton), modelli ufficiali dei fornitori, rework solo estetico.

| Parte | Componente reale | Modello in sim |
|---|---|---|
| Braccia + busto | Enactic OpenArm 2.0 bimanuale (7+7 DOF, QDD Damiao) | MJCF ufficiale `third_party/openarm_mujoco/v2` (Apache 2.0), coppie 40/27/7 Nm |
| Mani | Pinza OpenArm (default) / Inspire RH56DFTP (opzione) | MJCF ufficiale / URDF Unitree con mesh originali |
| Base | AgileX Tracer 2.0 (702×610×169 mm, 55 kg) | scatola con massa reale, 4 appoggi nel test di stabilità |
| Colonna | colonna elevabile corsa 400 mm (LINAK/igus) | giunto prismatico |
| Visione | RealSense D435i (testa, collo 2 assi) + D405 (polsi) | camere MuJoCo con FOV/risoluzione reali |
| Sicurezza | 2× SICK nanoScan3 (275°) + Pilz PNOZmulti 2 | `mj_multiRay` sulla scena, contorno appreso, campi ISO 13855 |

## Dipendenze esterne (non nel repository)
- `third_party/openarm_mujoco/` = MJCF ufficiale Enactic OpenArm 2.0 (github.com/enactic/openarm_mujoco, Apache-2.0)
- mani LEAP da mujoco_menagerie, Inspire da unitree_ros (solo opzioni)
- Blender 4.5 in `~/tools/blender-4.5.9-linux-x64/` per i render

## Comandi
```
cd ~/giorgio_sim
PY=~/IsaacLab/env_isaaclab/bin/python
$PY giorgio_real.py --look eva                  # GUI (eva | akira | gits | blame | cyber)
$PY giorgio_real.py --look akira --video video/x.mp4 --seconds 90
$PY giorgio_real.py --hands inspire             # mani Inspire (presa a script NON affidabile, vedi sotto)
$PY stability_test.py                           # analisi di ribaltamento
```

## Risultati (1 ottobre 2026)
- Kitting con pinza OpenArm: 8/8 flaconi (Ø50×160 mm, 0,35 kg) nel kit in 90 s, 0 persi, errore di posa 3–6 mm, ~7 s per flacone per braccio.
- Scanner: campo di protezione 1,72 m (ISO 13855: 1600 mm/s × 0,37 s + 1128 mm), avviso 2,82 m. Con operatore e passante: 3 arresti, 30 s rallentato, 25 s fermo su 90 s.
- Mani Inspire: montate e funzionanti, ma la presa di potenza programmata a script espelle il flacone. Va addestrata con teleoperazione/imitazione (leader arm OpenArm KER).
- Stabilità: vedi `video/stabilita.txt`.

## Versione 2 (2 ottobre 2026): corona sensori, carrello, costi ridotti
- Testa sostituita da **corona sensori fissa**: Insta360 X4 su asta (panoramica 360°, modalità webcam USB) + Orbbec Gemini 336L stereo inclinata di 35° sul banco. Niente collo motorizzato. Telecamere da polso: quelle incluse nel kit OpenArm 2.0.
- Base di default **carrello** (telaio in profilo di alluminio, 4 ruote con freno, 4 piedini stabilizzatori a vite su bracci sporgenti, 25 kg di zavorra). AMR Tracer 2.0 come opzione (`--base amr`).
- Gusci di design come mesh (`shells.py`), usati sia in MuJoCo sia in Blender (`render/blender_render.py`).
- Simulazione: 12/12 flaconi in 90 s, 0 persi, con operatore e passante. Stabilità (carrello): ribalta oltre 7,75 m/s² al lavoro, 4,5 m/s² nel caso peggiore; spinta per ribaltare 233 N a 1,25 m (~290 N con piedini a ±0,50 m).

### Distinta componenti v2 (prezzi senza IVA; "stima" dove non c'è un prezzo pubblico)
| Voce | € |
|---|---|
| OpenArm 2.0 bimanuale con pinze e telecamere da polso (6.000 $ ordine via e-mail) + spedizione/dazi | 5.950 |
| Insta360 X4 (stima prezzo di listino) | 500 |
| Orbbec Gemini 336L (379 $) | 340 |
| Mini-PC con GPU RTX (stima) | 1.400 |
| 2× SICK nanoScan3 Core + Pilz PNOZmulti 2 + relè ed arresto d'emergenza | 4.800 |
| Carrello: profili, ruote con freno, piedini, zavorra (stima) | 900 |
| Colonna manuale: profilo 80×80, slitta, morsetti (stima) | 250 |
| Alimentazione, cablaggi, connettori (stima) | 500 |
| Gusci SLS PA12 verniciati, piccola serie (stima) | 1.800 |
| Montaggio e collaudo, 30 h | 1.500 |
| **Totale Giorgio-P carrello** | **≈ 18.000** |
| Opzione AMR Tracer 2.0 + Jetson AGX Orin al posto del mini-PC + integrazione batteria | + 9.750 |
| Opzione mani LEAP (2× ~2.000 $, CAD solo non commerciale) / ORCA Lite (2× 1.500 $, CC BY 4.0) | + 3.600 / + 2.700 |

## Versione 3 (2 ottobre 2026): AMR che guida da A a B, collisioni vere, testa "cute"
- Base di default: **AgileX Tracer 2.0 fisico** (2 ruote motrici con motori a velocità e coppia limitata, 4 piroette, telaio con collisioni). Missione: stazione A → corsia (scanner in modalità marcia: campi che si allargano con la velocità, arresto per il passante) → aggancio sotto il banco B (pure pursuit + raddrizzamento sul posto; errore tipico 3 mm / 14 mm / 0,4°) → campi da fermo con contorno appreso → kitting sulla posa reale.
- Collisioni di colonna e busto contro l'ambiente; compensazione di gravità fatta dai motori (base libera).
- Testa fissa "cute": guscio tondo, frontale nero lucido con la Gemini 336L dietro, **due occhi = display rotondi GC9A01 1,28"** (~5–10 € l'uno) che guardano la persona più vicina, sbattono le palpebre e cambiano colore con lo stato di sicurezza (azzurro/giallo/rosso). Insta360 sopra la testa.
- Comandi: `giorgio_real.py` (AMR, default) · `--base cart` (carrello fisso).

## Versione 5–7 (notte 2–3 ottobre 2026): Giorgio fa tutto da solo, caffè vero sulla schiena, persone articolate
File principale: `giorgio_v5.py` (modello in `giorgio_model.py`). Comandi:
```
PY=~/IsaacLab/env_isaaclab/bin/python
MUJOCO_GL=egl $PY giorgio_v5.py --video video/v8_logistica.mp4 --seconds 185          # ciclo logistico completo (loop)
MUJOCO_GL=egl $PY giorgio_v5.py --agent "1:Giorgio, fammi un caffe e portalo a Marco" --video video/v8_caffe.mp4 --seconds 100
$PY giorgio_v5.py --agent "1:..."                                                     # GUI MuJoCo
MUJOCO_GL=egl $PY giorgio_v5.py --record render/rec_logistica.pkl ; cd render && $PY to_npz.py rec_logistica.pkl logistica
MUJOCO_GL=egl $PY pose_record.py render/rec_pose.pkl                                  # posa da studio per i render
render/run_stills_v7.sh ; render/run_video_v7.sh ; python render/compose.py render/edit_v7.json video/giorgio_presentazione.mp4
```
- **Niente pezzi dal nulla**: i flaconi stanno in un vassoio di kitting sul banco A; Giorgio li trova con la Gemini 336L e li carica da solo (6 nel vassoio frontale con imbocchi svasati da 16 mm, 2 nelle pinze). La posa del flacone in pinza viene stimata (telecamera di polso) e compensata al rilascio: 6/6 nel vassoio entro 7 mm.
- **Ciclo chiuso**: B → visione 8/8 fori (errore 1,8 mm) → 8/8 inseriti → Giorgio torna al punto di attesa davanti ad A; l'operatore con la cassetta svuota B a mano, porta i flaconi in A e li rimette nel vassoio; Giorgio riaggancia. Stato finale = iniziale (video in loop), ~160 s.
- **Caffè vero, integrato sulla schiena**: De'Longhi Nespresso Inissia EN80 su mensola dietro la colonna. Il braccio destro prende un bicchiere dalla pila, lo posa sulla navetta (attuatore lineare 150 mm sul supporto tazzina ribaltabile della Inissia), preme il pulsante sulla testa della macchina; la navetta porta il bicchiere sotto l'erogatore e lo riporta fuori; il braccio prende il caffè pieno e lo porta alla persona. Tutte le pose verificate con IK (una presa laterale sotto la testa NON è raggiungibile: per questo la navetta).
- **Consegna**: Giorgio si ferma davanti a Marco, allunga il braccio; Marco si avvicina, allunga la mano, prende il bicchiere (la pinza si apre), lo porta alla scrivania e lo appoggia.
- **Persone articolate** (17 pezzi: ginocchia, gomiti, mani, capelli/casco, gilet): camminata con avvio/arresto morbidi, testa che guarda il robot, cassetta, presa con IK a 2 segmenti; cedono il passo al robot (distanza minima persona-robot nel ciclo 0,76 m dal centro base) e ripianificano se bloccate.
- **Frenata**: la velocità in arrivo è limitata dallo spazio di arresto con strappo limitato e ritardo; tolto l'azzeramento brusco dei motori (era la causa dell'"imbarcata"). Beccheggio dinamico in frenata ≈ 0,35° (prima 2,4°); i picchi a ~0,9° sono statici, da bracci in avanti con carico, a robot fermo.
- **Scanner**: contorno appreso solo a base ferma (niente falsi arresti dopo l'aggancio).
- **Baffi**: fissi, diffusore stampato in PETG traslucido con LED dietro (colore = stato: azzurro/ambra/rosso, ambra in modalità caffè). Opzione con 2 micro-servo non usata.

### Distinta componenti v7 (prezzi senza IVA)
| Voce | € |
|---|---|
| Enactic OpenArm 2.0 bimanuale con pinze e telecamere di polso | 5.950 |
| AgileX Tracer 2.0 | 7.500 |
| Orbbec Gemini 336L | 340 |
| Insta360 X4 | 500 |
| NVIDIA Jetson AGX Orin 64 GB | 3.150 |
| 2× SICK nanoScan3 + Pilz PNOZmulti 2 + arresto d'emergenza | 4.800 |
| Vassoio, colonna, staffe | 500 |
| Gusci SLS PA12 verniciati | 1.800 |
| Occhi GC9A01 + LED baffi + striscia LED | 40 |
| Zaino caffè: De'Longhi Inissia + navetta lineare + porta-bicchieri | 250 |
| Stazione di ricarica | 900 |
| Cablaggi e alimentazione | 600 |
| Montaggio e collaudo (35 h) | 1.750 |
| **Costo** | **≈ 28.080** |
| **Prezzo al cliente (margine 30% sul prezzo: 28.080 / 0,70)** | **≈ 40.100** → listino 39.900 (early bird) / 42.900 |

Kickstarter: bozze in `kickstarter/` (campagna IT/EN, script video, post di lancio). Vincoli: serve un prototipo fisico funzionante, niente render fotorealistici spacciati per prodotto, ricompensa massima 8.500 € per progetti dall'Italia (il robot completo è un deposito).
