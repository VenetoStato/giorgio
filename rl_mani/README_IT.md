# rl_mani: rotazione di un cubo in mano con la mano ORCA v2 (RL)

La mano destra ORCA v2 (open source, CC BY 4.0) sta col palmo in su e deve far ruotare un cubo
da 5–6 cm attorno all'asse verticale (+z, in senso antiorario visto dall'alto) senza farlo
cadere. La politica è appresa con PPO su 4096 ambienti paralleli in GPU (mujoco_warp). Non
c'è nessun movimento scriptato: l'andatura delle dita (finger gaiting) è emersa durante
l'addestramento.

## File
| file | cosa contiene |
|---|---|
| `build_model.py` | genera `orca_cubo_rl.xml` a partire dai file ORCA originali, senza modificarli |
| `orca_cubo_rl.xml` | MJCF usato per addestramento, video e Blender (i percorsi delle mesh sono assoluti) |
| `env_orca.py` | ambiente vettorizzato su GPU (mujoco_warp + torch), con ricompensa e randomizzazione |
| `train.py` | PPO compatto scritto per questo progetto (actor-critic MLP) |
| `valuta_e_video.py` | metriche su N episodi, video offscreen e traiettoria `.npz` |
| `grafico.py` | genera `curva_apprendimento.png` da `runs/r1/log.csv` |
| `politica_orca_cubo.pt` | politica addestrata (= `runs/r1/modello.pt`, iterazione 2400) |
| `runs/r1/` | log CSV e checkpoint intermedi (iniziale, 100, 300, 1000) |
| `valutazione/m*.json` | risultati numerici delle valutazioni |
| `prima.mp4`, `dopo.mp4` | video 1920x1080 a 30 fps |
| `traiettoria_dopo.npz` | per ogni frame (30 fps): `qpos`, `xpos`, `xquat` di tutti i body, più `body_names`, `joint_names`, `mjcf` (percorso del modello), `lato_cubo_m` |

## Modello
- ORCA v2 destra, polso bloccato (giunto `right_wrist` rimosso): **16 DOF attuati**
  (abduzione, MCP e PIP per ogni dito; per il pollice CMC, abduzione, MCP e PIP). Gli attuatori
  di posizione sono quelli originali (kp=2, coppia massima ±1 N·m).
- Le collisioni usano primitive al posto delle mesh: capsule per le falangi, box per palmo e
  avambraccio, stimate con la PCA dei vertici delle mesh. Le mesh restano solo visive. Le
  collisioni tra un dito e l'altro sono attive.
- Il cubo è libero, di massa nominale 60 g e lato 5,5 cm, con facce colorate solo visive.
- dt fisico 5 ms, controllo a 25 Hz (8 sotto-passi), cono di attrito ellittico, impratio 2.

## Osservazioni (64)
Posizione dei giunti e target correnti (normalizzati in [-1,1]), velocità dei giunti,
posizione del cubo rispetto al centro del palmo, orientamento del cubo (rappresentazione 6D),
velocità lineare e angolare del cubo, velocità di rotazione attorno a z al passo precedente.
Si aggiunge rumore gaussiano con σ = 0,01.
**Attenzione:** la politica vede lo stato del cubo in modo privilegiato (è il simulatore a
fornirlo). Sul robot reale questo dato non è disponibile così com'è: vedi la sezione sim-to-real.

## Azioni (16)
Incrementi del target di posizione: `target += 0.1 rad · clip(a, -1, 1)`. Il target resta poi
limitato al ctrlrange del giunto.

## Ricompensa (per passo di controllo)
- `+clip(ω_z, -0.5, 1.2)`: velocità di rotazione del cubo attorno alla verticale, ricavata dal
  quaternione (componente twist)
- `-2·d_xy`: distanza orizzontale del cubo dal centro del palmo
- `-0.05·|ω_xy|` (ribaltamento) e `-0.3·|v|` (velocità lineare del cubo)
- `-0.02·|Δtarget|²` normalizzato e `-0.05·Σ τ²`, per avere movimenti dolci e coppie basse
- `-20` se il cubo cade, cioè scende sotto il piano del palmo o si allontana di più di 7,5 cm
  dal suo centro. In quel caso l'episodio termina.

Un episodio dura 16 s (400 passi). Il cubo parte con yaw casuale e un offset di ±1 cm; le dita
partono dalla posa iniziale con un rumore di ±0,08 rad.

## Randomizzazione di dominio (a ogni reset, per ambiente)
Lato del cubo 5,0–6,0 cm, massa 30–120 g (inerzia coerente), attrito 0,5–1,2 (stesso valore su
mano e cubo, perché MuJoCo usa il massimo dei due), kp attuatori ×0,75–1,25, smorzamento dei
giunti ×0,7–1,4. In più, spinte casuali sul cubo (con probabilità 2% per passo, forza
σ = 0,1 N che poi decade) e il rumore sulle osservazioni.

## Iperparametri PPO
4096 ambienti, orizzonte di 24 passi (98 304 campioni per iterazione), 5 epoche, 4 minibatch,
γ = 0,99, λ = 0,95, clip 0,2, value clipping, learning rate adattivo con KL obiettivo 0,016
(partenza 3e-4), entropia 0,002, gradiente limitato a norma 1. Reti MLP 512-256-128 ELU,
separate per attore e critico. Normalizzazione delle osservazioni con media e varianza mobili.
Deviazione standard iniziale 0,6.

## Risultati (run r1)
- Addestramento: **236 M passi di ambiente** (checkpoint usato, iterazione 2400) in **81 minuti**
  di tempo reale su RTX 5070, circa 49 000 passi/s inclusa la PPO. VRAM usata circa 1,9 GB.
- Valutazione su 50 episodi da 10 s, politica deterministica (file `valutazione/m*.json`):

| politica | condizioni | rad / 10 s (media) | giri / 10 s | episodi con caduta |
|---|---|---|---|---|
| non addestrata | con randomizzazione e spinte | 0,04 | 0,006 | 16 % |
| non addestrata | nominale | 0,02 | 0,003 | 8 % |
| non addestrata, stocastica | con randomizzazione e spinte | 0,17 | 0,03 | 42 % |
| **addestrata** | con randomizzazione e spinte | **12,7** | **2,0** | **2 %** (1/50) |
| addestrata | nominale (cubo 5,5 cm, nessuna spinta) | 11,7 | 1,9 | 4 % (2/50) |
| addestrata, 500 episodi | con randomizzazione e spinte | 13,1 | 2,1 | 3,2 % |
| addestrata, 50 episodi da 60 s | con randomizzazione e spinte | 13,8 | 2,2 | 6 % in 60 s |

- Video: in `dopo.mp4` il cubo ruota di 20,7 rad (3,3 giri) in 15 s senza cadere.
- La curva "episodi terminati per caduta" all'inizio è distorta: nelle prime iterazioni gli
  unici episodi che si concludono sono quelli finiti con una caduta.

## Come rieseguire
```bash
PY=${PYTHON:-python}   # ambiente di addestramento: requirements-train.txt (mujoco 3.5, mujoco_warp 3.5, warp 1.12, torch CUDA)
cd rl_mani
$PY build_model.py                                  # rigenera orca_cubo_rl.xml
$PY env_orca.py 4096                                # benchmark (~125k passi di controllo/s)
$PY train.py --envs 4096 --max_minutes 90 --out runs/r2
$PY grafico.py runs/r2/log.csv curva_apprendimento.png
$PY valuta_e_video.py metriche runs/r2/modello.pt --n 50
$PY valuta_e_video.py video runs/r2/modello_iniziale.pt --stocastica --secondi 8 --out prima.mp4
$PY valuta_e_video.py video runs/r2/modello.pt --secondi 15 --out dopo.mp4 --npz traiettoria_dopo.npz
```
`train.py` dipende da `mjlab` (presente nello stesso env) soltanto per `expand_model_fields`.

## Limiti e sim-to-real (in onestà)
- **Stato privilegiato:** la politica conosce posa e velocità del cubo. Per la mano reale serve
  una di queste strade: distillarla in una politica "studente" che usa solo propriocezione e
  storia dei giunti (approccio Hora/RMA), oppure stimare la posa del cubo con una camera
  (D405 sul polso, marker o pose estimation) e addestrare con il ritardo e il rumore di quella
  stima.
- **Attuatori:** la ORCA reale muove le dita con tendini e motori Dynamixel nell'avambraccio.
  Qui ogni giunto è un servo di posizione ideale (kp=2, ±1 N·m). Bisogna identificare la
  risposta reale (attrito dei tendini, isteresi, backlash, latenza del bus, banda) e inserirla
  nel modello, per esempio con una rete attuatore o un modello di tendine. Va randomizzata
  anche la latenza dell'azione, che qui non c'è.
- **Contatto:** le collisioni sono capsule e box, non le superfici reali. La pelle morbida
  della ORCA e la sua cedevolezza non sono modellate, e l'attrito è coulombiano con un unico
  coefficiente. Nel log compaiono avvisi `ccd_iterations` (box-box cubo-palmo): sono innocui,
  ma conviene aumentarli.
- **Comportamento:** la politica ruota a circa 1,3 rad/s, sopra il tetto della ricompensa
  (1,2 rad/s), con movimenti rapidi delle dita. Sul reale andrebbero limitate di più velocità
  e jerk (penalità più alte, filtro sull'azione) per non usurare i tendini.
- La randomizzazione copre dimensioni, massa e attrito del cubo, guadagni, smorzamento e
  spinte. Non copre la gravità inclinata (polso orientato diversamente), forme diverse dal
  cubo, errori di calibrazione dei giunti e il ritardo di osservazione.
