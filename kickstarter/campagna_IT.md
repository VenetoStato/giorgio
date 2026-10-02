# Giorgio — pagina campagna Kickstarter (IT)

> **Titolo (53/60):** Giorgio: il robot di servizio open che porta il caffè
>
> **Sottotitolo (122/135):** Un robot mobile a due braccia costruito con parti open e acquistabili. Logistica, visione, caffè. E lo puoi modificare tu.
>
> **Categoria:** Technology → Robots · **Luogo:** Italia · **Valuta:** EUR · **Durata:** 30 giorni · **Obiettivo:** € 120.000

> **[DA AGGIORNARE AL LANCIO — STATO DEL PROTOTIPO]** Kickstarter chiede, per i progetti hardware, un prototipo funzionante e non ammette render fotorealistici. Prima del lancio sostituire le immagini segnate "render" con foto e video del prototipo fisico e aggiornare questo riquadro con ciò che il prototipo fa davvero. Vedi `README.md`.

![Giorgio — render/simulazione, da sostituire con foto del prototipo](../render/stills/hero.png)

---

## In breve

**Giorgio è un robot di servizio mobile a due braccia, open hardware, costruito con parti open e acquistabili.**
Va da A a B in mezzo alle persone e rallenta quando ti avvicini. Inserisce pezzi in una maschera guidato dalla visione. Ti fa un caffè e te lo porta in mano. Gli parli in italiano: *"Giorgio, fammi un caffè e portalo a Marco."*

Non è un umanoide chiuso da centinaia di migliaia di euro. È una piattaforma che puoi aprire, capire, riparare e insegnare: **la tua piattaforma open per le attività della tua azienda.**

E alla peggio, è una costosa macchinetta del caffè.

**Dove siamo oggi, senza giri di parole:** tutto quello che vedi in questa pagina è stato dimostrato **in simulazione fisica** (MuJoCo, con i modelli ufficiali dei fornitori). Questa campagna serve a costruire i primi Giorgio fisici, a portarli fuori dal computer e a fare il lavoro serio sulla sicurezza.

---

## La storia

Negli ultimi due anni sono usciti robot umanoidi bellissimi. Video perfetti, design da studio, promesse enormi. Quasi tutti hanno una cosa in comune: sono **chiusi**. Non sai cosa c'è dentro, non puoi ripararli, non puoi cambiare una riga di codice, e spesso non puoi nemmeno comprarli.

Nel frattempo, il mondo open ha fatto passi da gigante. **OpenArm 2.0** di Enactic è un busto a due braccia da 7+7 gradi di libertà, con motori QDD, hardware e software rilasciati sotto Apache-2.0. Le basi mobili per la logistica sono un prodotto maturo. Gli scanner laser di sicurezza certificati si comprano a catalogo. I modelli linguistici sanno trasformare una frase in un piano.

Ci siamo chiesti: **e se mettessimo insieme i pezzi migliori, già esistenti, e ci aggiungessimo solo quello che manca?** Un corpo bello, una faccia simpatica, la sicurezza fatta bene, un cervello che capisce l'italiano. E una macchinetta del caffè sulla schiena, perché un robot che entra in ufficio deve prima di tutto farsi voler bene.

Così è nato Giorgio.

---

## Cos'è Giorgio

![Vista esplosa delle parti — render, da sostituire con foto/CAD](../render/stills/exploded.png)

Giorgio è fatto di quattro strati, tutti riconoscibili:

1. **Base mobile** — AgileX Tracer 2.0, un AMR differenziale commerciale (702 × 610 mm, 55 kg), supportato in ROS.
2. **Sicurezza** — due scanner laser di sicurezza SICK nanoScan3 e un relè di sicurezza Pilz PNOZmulti 2: componenti certificati, campi di protezione calcolati secondo ISO 13855.
3. **Busto e braccia** — Enactic OpenArm 2.0 bimanuale (7+7 DOF, motori QDD Damiao), con pinze parallele e telecamere da polso OpenArm.
4. **Testa e sensi** — una testa tonda con due occhi-display rotondi, i **baffi retroilluminati** (sì, i baffi sono la nostra firma), una telecamera stereo Orbbec Gemini 336L per la manipolazione, una Insta360 X4 a 360° su un'asta corta per vedere chi c'è intorno, e un NVIDIA Jetson AGX Orin come cervello di bordo.

Sopra a tutto: gusci bianchi satinati soft-touch (SLS PA12 verniciato), un volto in vetro scuro e un accento arancione. Un'estetica da studio di design, costruita su un'ossatura che puoi comprare pezzo per pezzo.

![Il volto di Giorgio — render, da sostituire con foto](../render/stills/face.png)

**Gli occhi** sono due display rotondi GC9A01 da 1,28". Guardano la persona più vicina, sbattono le palpebre e cambiano colore con lo stato di sicurezza:

| Colore occhi | Significato |
|---|---|
| Blu | tutto ok, area libera |
| Ambra | sto rallentando (qualcuno è nel campo di avviso) — oppure *modalità caffè* |
| Rosso | fermo (qualcuno è nel campo di protezione) |

Una striscia LED attorno alla base ripete lo stato, così lo vedi anche da dietro.

---

## Cosa fa (in simulazione, oggi)

### 1. Logistica in mezzo alle persone

![Logistica con persone — simulazione](../render/stills/logistics.png)

Giorgio percorre un giro logistico da A a B con guida morbida a jerk limitato: in frenata il busto beccheggia di circa **0,4°** (ruote piroettanti sospese, modellate in simulazione). Quando una persona attraversa il percorso, Giorgio **rallenta in modo visibile** nel campo di avviso e **si ferma** nel campo di protezione. Gli occhi diventano ambra, poi rossi. Quando la persona se ne va, riparte.

### 2. Inserimento con la visione

Alla stazione di lavoro Giorgio usa la telecamera stereo per localizzare i pezzi e inserirli in una maschera: **8 pezzi su 8 inseriti**, con un errore di visione di circa **1,6 mm**, in simulazione.

### 3. Caffè, dalla capsula alla mano

![Il caffè — render/simulazione](../render/stills/coffee.png)

Sulla schiena di Giorgio c'è uno zaino-caffè: una **macchina a capsule commerciale** di serie (non vincolata a una marca: va bene qualsiasi modello compatto con pulsante sulla testa), una pila di bicchierini e una piccola navetta con attuatore lineare sul supporto tazza ribaltabile.

- il braccio destro prende un bicchiere e lo appoggia sulla navetta;
- preme il pulsante della macchina (non la modifichiamo: la usa come la useresti tu);
- la navetta porta il bicchiere sotto l'erogatore e lo riporta indietro;
- il braccio prende il bicchiere pieno, Giorgio guida fino alla persona e **te lo porge**.

Durante la preparazione gli occhi sono ambra: *modalità caffè*.

### 4. Gli parli, lui pianifica

> *"Giorgio, fammi un caffè e portalo a Marco."*

Il controllo è a due livelli, come il pensiero veloce e lento:

- **Sistema 1 (veloce):** un router di comandi e abilità basato su regole, risponde in **meno di 1 ms** ai comandi semplici ("fermati", "vai alla stazione B"). Funziona anche senza rete.
- **Sistema 2 (ragionato):** un planner basato su un modello linguistico (oggi Claude di Anthropic, via API cloud) trasforma frasi complesse in un piano di abilità:

```
fai_caffe → porta_caffe(Marco) → di("Ecco il tuo caffè, Marco!") → ricarica
```

Abilità disponibili oggi: `vai_a`, `fai_caffe`, `porta_caffe`, `carica`, `scarica_e_inserisci`, `ricarica`, `di`. Quando la batteria è bassa, Giorgio va alla **stazione di ricarica** e si aggancia da solo.

Il planner non comanda direttamente i motori e non tocca la sicurezza: sceglie **quali abilità** eseguire. Gli scanner e il relè di sicurezza lavorano sempre, in modo indipendente dal software.

---

## Cosa è open e cosa no (onestamente)

Diciamo "open" solo dove lo è davvero.

| Parte | Componente | Stato |
|---|---|---|
| Braccia + busto | Enactic OpenArm 2.0 (7+7 DOF) | **Open source** — hardware CERN-OHL-S-2.0, software Apache-2.0 |
| Pinze + telecamere polso | kit OpenArm 2.0 | **Open source** (parte di OpenArm) |
| Motori | Damiao QDD | commerciali (dentro OpenArm) |
| Base mobile | AgileX Tracer 2.0 | **Commerciale off-the-shelf**, supporto ROS — non è open hardware |
| Scanner di sicurezza | 2× SICK nanoScan3 | commerciali, certificati |
| Relè di sicurezza | Pilz PNOZmulti 2 | commerciale, certificato |
| Visione manipolazione | Orbbec Gemini 336L | commerciale, SDK pubblico |
| Visione 360° | Insta360 X4 | commerciale |
| Calcolo | NVIDIA Jetson AGX Orin | commerciale |
| Macchina del caffè | macchina a capsule compatta, marca a scelta | commerciale, di serie, non modificata |
| Planner LLM | Claude (Anthropic), API cloud | servizio commerciale, sostituibile |
| **Gusci, colonna, supporti, testa** | progetto Giorgio | **Open** — CAD/STL rilasciati (licenza proposta: CERN-OHL-W 2.0) |
| **Volto: occhi + baffi + LED** | progetto Giorgio | **Open** — schemi e firmware (licenza proposta: CERN-OHL-W 2.0 / Apache-2.0) |
| **Zaino-caffè: navetta + supporti** | progetto Giorgio | **Open** — CAD + firmware |
| **Software: abilità, router, agente, simulazione** | progetto Giorgio | **Open** — Apache-2.0 (proposta) |
| Mani abili (opzione) | ORCA Hand / Pollen AmazingHand | **Open, uso commerciale consentito**: ORCA CC BY 4.0 (software MIT), AmazingHand CC BY 4.0 (software Apache-2.0). Montate e provate in simulazione su gesti e pulsanti; le prese si insegnano. (LEAP Hand e Aero Hand: CAD solo non commerciale, quindi escluse.) |

In pratica: **la parte che costruiamo noi è tutta open.** Quello che compriamo, lo compriamo da chi lo fa meglio — e te lo diciamo.

---

## Sicurezza: la parte noiosa che conta di più

![Campi di sicurezza — simulazione](../render/stills/safety.png)

Un robot che gira tra le persone deve sapere quando fermarsi. Non lo lasciamo fare a una rete neurale.

- **2× SICK nanoScan3** coprono il perimetro della base.
- **Pilz PNOZmulti 2** gestisce arresti di emergenza e campi di sicurezza.
- **Campi dipendenti dalla velocità, secondo ISO 13855:** a robot fermo il campo di protezione è di **1,72 m**, calcolato con la velocità di avvicinamento di una persona di 1,6 m/s (1.600 mm/s × 0,37 s + 1.128 mm). Più Giorgio va veloce, più i campi si allargano.
- **Campo di avviso → rallenta. Campo di protezione → si ferma.** Sempre, indipendentemente da cosa sta pensando il planner.
- Pulsante di arresto d'emergenza fisico sul robot.

**Quello che Giorgio NON è ancora:** una macchina certificata. I componenti di sicurezza sono certificati, ma **la macchina integrata ha bisogno della sua valutazione dei rischi e della marcatura CE** secondo il Regolamento Macchine (UE) 2023/1230 prima di poter essere venduta come prodotto finito nell'UE. Una parte importante di questa campagna paga proprio questo lavoro. Fino ad allora Giorgio è una **piattaforma di sviluppo**, da usare in aree controllate e da personale formato.

---

## Perché open

- **Puoi ripararlo.** Si rompe un guscio? Lo ristampi. Si rompe un motore? È un pezzo a catalogo.
- **Puoi capirlo.** Il codice delle abilità, dell'agente e della simulazione è lì, leggibile.
- **Puoi insegnargli il tuo lavoro.** Le attività di un'azienda non sono quelle di un video promozionale. Con una piattaforma open, le abilità le scrivi (o le insegni) tu.
- **Non resti ostaggio di nessuno.** Se domani noi spariamo, Giorgio continua a funzionare: i pezzi si comprano, i file sono pubblici.

Giorgio nasce come alternativa ai grandi umanoidi chiusi — pensiamo a progetti come GENE.01 di Generative Bionics — con una scelta diversa: **niente parti segrete, solo parti open e acquistabili, più un lavoro di design sopra.** *(Generative Bionics e GENE.01 sono citati solo come confronto; nessuna affiliazione.)*

---

## Specifiche (progetto v5, ottobre 2026)

| | |
|---|---|
| Braccia | OpenArm 2.0 bimanuale, 7+7 DOF, QDD Damiao |
| Pinze | pinze parallele OpenArm (default) |
| Mani abili | ORCA Hand / AmazingHand — **opzione**, prese da addestrare |
| Base | AgileX Tracer 2.0, differenziale, 702 × 610 mm, 55 kg (sola base) |
| Ingombro / altezza / massa totale | [da misurare sul prototipo] |
| Sicurezza | 2× SICK nanoScan3, Pilz PNOZmulti 2, e-stop; campi ISO 13855 (protezione 1,72 m da fermo) |
| Visione | Orbbec Gemini 336L (testa), telecamere polso OpenArm, Insta360 X4 360° su asta |
| Calcolo | NVIDIA Jetson AGX Orin |
| Volto | 2× display rotondi GC9A01 1,28", baffi LED retroilluminati, striscia LED di stato |
| Caffè | macchina a capsule compatta (marca a scelta), navetta ad attuatore lineare, pila di bicchierini |
| Controllo | Sistema 1 (router < 1 ms, offline) + Sistema 2 (planner LLM, cloud) |
| Ricarica | stazione di aggancio automatica |
| Autonomia, velocità massima di lavoro | [da definire con il prototipo e la valutazione dei rischi] |
| Gusci | SLS PA12, verniciati bianco satinato soft-touch, volto vetro scuro, accento arancione |
| Software | ROS-compatibile, simulazione MuJoCo inclusa |

---

## Quanto costa Giorgio, e perché

Ti mostriamo i conti. Prezzi in euro, IVA esclusa.

| Voce | € |
|---|---:|
| OpenArm 2.0 bimanuale (pinze + telecamere polso, spedizione/dazi) | 5.950 |
| AgileX Tracer 2.0 | 7.500 |
| Orbbec Gemini 336L | 340 |
| Insta360 X4 | ~500 |
| NVIDIA Jetson AGX Orin | 3.150 |
| Sicurezza: 2 scanner + PNOZ + e-stop | 4.800 |
| Piano, colonna, supporti | 500 |
| Gusci SLS PA12 verniciati | 1.800 |
| Occhi + LED | 40 |
| Zaino-caffè (macchina a capsule + attuatore navetta + porta-bicchieri) | ~250 |
| Stazione di ricarica | 900 |
| Cablaggi e alimentazione | 600 |
| Montaggio e collaudo (35 h) | 1.750 |
| **Costo totale** | **≈ 28.080** |

Con un margine del 30% sul prezzo: **28.080 ÷ 0,70 ≈ 40.100 €**.

- **Early bird Fondatori: 39.900 € + IVA** (margine ≈ 29,6%): un piccolo sconto per chi si prende il rischio con noi per primo.
- **Prezzo Pioneer / listino: 42.900 € + IVA** (margine ≈ 34,5%): copre oscillazioni del dollaro (OpenArm è prezzato in USD), garanzia e spedizione in UE.

---

## Ricompense

> **Nota importante su Kickstarter:** per i progetti con sede in Italia Kickstarter non ammette ricompense sopra **8.500 €**. Per questo il Giorgio completo si prenota con un **acconto** su Kickstarter; il saldo si regola con un contratto separato prima della consegna. Gli importi delle ricompense fino a 5.900 € includono l'IVA; i prezzi del Giorgio completo sono IVA esclusa (clienti business).

### € 25 — Sostenitore
Il tuo nome inciso sulla **targa posteriore** dei primi Giorgio fisici, aggiornamenti dal laboratorio, sfondo "baffi" in alta risoluzione.
*Consegna stimata: dicembre 2027 (foto della targa).*

### € 49 — Kit digitale gusci
I file **STL/CAD dei gusci e dei supporti** di Giorgio con la **guida di montaggio** completa, in anticipo rispetto al rilascio pubblico, e accesso al canale dei costruttori. (Rilasceremo tutto open comunque: qui paghi per averlo prima e per sostenerci.)
*Consegna stimata: maggio 2027 (gusci v1) · guida finale dicembre 2027.*

### € 149 — Giorgio Face
Il **kit volto**: due display rotondi GC9A01 1,28", scheda di controllo, baffi LED retroilluminati con diffusore, cavi. **Firmware open**, comandabile via USB/ROS. Gli occhi seguono un punto, sbattono le palpebre, cambiano colore. Da mettere sul tuo robot — o sulla tua scrivania. Spedizione a parte.
*Consegna stimata: settembre 2027.*

### € 1.190 — Zaino-caffè per OpenArm
Per chi ha già un **OpenArm 2.0**: supporto per macchina a capsule compatta (la macchina la scegli tu), navetta ad attuatore lineare con elettronica, porta-bicchieri, piastra di montaggio, abilità `fai_caffe` open e guida di taratura. Non include braccio né base.
*Consegna stimata: dicembre 2027.*

### € 4.900 — Adotta Giorgio per una settimana (limitato: 6)
Un Giorgio prototipo viene **nella tua azienda per 5 giorni lavorativi**, con un nostro tecnico, su un'attività concordata (logistica interna, servizio caffè in un'area controllata). Include sopralluogo e valutazione dei rischi del sito. Nord e Centro Italia; altre zone su richiesta. Rivolto ad aziende.
*Periodo stimato: marzo – giugno 2028.*

### € 5.900 — Giorgio Body Kit (fai da te, limitato: 20)
Tutto il **corpo di Giorgio senza le parti che si comprano da altri**: gusci verniciati, colonna, piano e supporti, testa con kit volto, cablaggi, file di configurazione della sicurezza, software. **Non include** OpenArm, Tracer 2.0, scanner/relè di sicurezza, Jetson, telecamere e macchina del caffè: ti diamo la lista d'acquisto esatta.
*Consegna stimata: gennaio 2028.*

### € 8.500 — Giorgio Fondatori: acconto (limitato: 5)
Prenota uno dei **primi 5 Giorgio completi** al prezzo early bird di **39.900 € + IVA**. Gli 8.500 € sono un acconto scalato dal prezzo; il saldo (31.400 € + IVA) si regola con contratto separato prima della spedizione. Include una giornata di formazione e il tuo nome sulla targa.
*Consegna stimata: settembre 2028.*

### € 5.000 — Giorgio Pioneer: acconto (limitato: 10)
Prenota un **Giorgio completo** al prezzo di **42.900 € + IVA**, con acconto di 5.000 € scalato dal prezzo e saldo (37.900 € + IVA) con contratto separato.
*Consegna stimata: dicembre 2028.*

> Il Giorgio completo viene consegnato come **piattaforma di sviluppo** con la documentazione di sicurezza disponibile in quel momento. Se la marcatura CE della macchina integrata non fosse completata entro la consegna, lo diciamo prima del saldo e potrai scegliere se attendere o recedere con rimborso dell'acconto (al netto delle commissioni della piattaforma). [termini da validare con un legale]

---

## Obiettivo e uso dei fondi — € 120.000

| Voce | € |
|---|---:|
| Due Giorgio fisici completi (uno per collaudo e valutazione CE, uno per i piloti) | 56.200 |
| Valutazione dei rischi, validazione funzioni di sicurezza, consulenza CE (Reg. UE 2023/1230) | 18.000 |
| Attrezzature: setup gusci in piccola serie, maschere di montaggio e verniciatura | 8.000 |
| Raccolta dati per le mani abili (teleoperazione, una coppia di mani) | 6.000 |
| Team: 6 mesi di integrazione e passaggio simulazione → realtà | 20.000 |
| Commissioni Kickstarter e pagamenti (~8%) | 9.600 |
| Imprevisti | 2.200 |
| **Totale** | **120.000** |

Le ricompense fisiche (Face, zaino-caffè, Body Kit, Giorgio completi) hanno un loro margine e non mangiano questo budget.

---

## Obiettivi aggiuntivi (stretch goals)

- **€ 150.000 — Mani abili, sul serio.** Pubblichiamo un dataset open di dimostrazioni teleoperate e le politiche addestrate per ORCA e AmazingHand sulle abilità di Giorgio.
- **€ 200.000 — Colonna motorizzata.** Opzione colonna elevabile (corsa 400 mm) per lavorare dal pavimento al bancone.
- **€ 250.000 — Pacchetto abilità "accoglienza".** Riconoscimento e saluto delle persone a 360°, accompagnamento ospiti, consegna oggetti in reception.
- **€ 300.000 — Un Giorgio per la comunità.** Un terzo Giorgio dato in uso a un'università o a un makerspace italiano, aperto a chi vuole sviluppare abilità.

---

## Tabella di marcia

| Quando | Cosa |
|---|---|
| Ott 2026 (fatto) | Progetto v5 completo in simulazione: logistica A→B, inserimento con visione 8/8, caffè e consegna, comandi in linguaggio naturale |
| Q4 2026 – Q1 2027 | [prerequisito al lancio] primo prototipo fisico, foto e video reali |
| Lancio campagna | [data da definire] — 30 giorni |
| Mag 2027 | Kit digitale gusci v1 ai sostenitori |
| Q2 – Q3 2027 | Ordini OpenArm e Tracer per i due Giorgio della campagna; assemblaggio; prove su strada in area controllata |
| Set 2027 | Spedizione Giorgio Face |
| Q4 2027 | Validazione funzioni di sicurezza; zaino-caffè per OpenArm (dic) |
| Gen 2028 | Spedizione Body Kit |
| Q1 2028 | Valutazione dei rischi e fascicolo tecnico CE |
| Mar – Giu 2028 | Settimane pilota in azienda |
| Set 2028 | Consegna Giorgio Fondatori |
| Dic 2028 | Consegna Giorgio Pioneer |

---

## Rischi e sfide

Ti diciamo dove può andare storto.

- **Simulazione ≠ realtà.** I risultati di questa pagina vengono da una simulazione fisica accurata, con i modelli ufficiali dei fornitori. Ma la realtà ha attriti, cavi, luce, pavimenti sporchi. Ci aspettiamo settimane di messa a punto: errore di visione, presa, frenata, aggancio alla ricarica. Abbiamo messo a budget tempo per questo, e lo racconteremo negli aggiornamenti, anche quando non va bene.
- **Mani abili.** Le mani articolate open (ORCA, AmazingHand) sono montabili, ma **oggi le prese programmate a script non sono affidabili**: serve raccogliere dati in teleoperazione e addestrare per imitazione. Per questo il Giorgio di serie usa le pinze parallele. Le mani sono un'opzione sperimentale, non una promessa.
- **Marcatura CE.** La valutazione dei rischi può richiedere modifiche (velocità più basse, campi più grandi, protezioni aggiuntive). Se la marcatura richiede più tempo, le consegne del Giorgio completo slittano: preferiamo così.
- **Fornitura OpenArm e altri componenti.** OpenArm 2.0 si ordina da Enactic, con tempi e prezzi in dollari che possono cambiare; lo stesso vale per Tracer, Jetson e scanner. Abbiamo margine per le oscillazioni, non per una crisi di fornitura: in quel caso ritarderemo e lo comunicheremo subito.
- **Dipendenza dal cloud.** Il planner del Sistema 2 oggi usa un modello linguistico via API: senza rete Giorgio esegue i comandi diretti del Sistema 1, ma non pianifica frasi complesse. Stiamo valutando planner locali sulla Jetson.
- **Macchina del caffè.** Usiamo una macchina a capsule di serie, non modificata, in un modo per cui non è stata progettata (la preme un robot): la garanzia del produttore potrebbe non coprire questo uso.
- **Siamo una squadra piccola.** [da completare: esperienza del team nella costruzione di hardware]

---

## FAQ

**Giorgio esiste?**
Il progetto completo esiste ed è stato verificato in simulazione fisica. [DA AGGIORNARE AL LANCIO: descrizione del prototipo fisico.] I fondi della campagna servono a costruire i Giorgio fisici e a certificarli.

**È un umanoide?**
Ha un busto, due braccia a 7 gradi di libertà, una testa e una faccia. Si muove su ruote, non su gambe: in ufficio e in magazzino le ruote sono più sicure, più efficienti e più economiche.

**Posso usarlo in azienda da subito?**
Come piattaforma di sviluppo, in un'area controllata e con personale formato, sì. Come macchina marcata CE per uso generale, non ancora: è uno degli obiettivi della campagna.

**Perché non usate una base open?**
Perché non ne abbiamo trovata una matura con la stessa affidabilità e supporto ROS. La Tracer 2.0 è commerciale e lo diciamo. Se ne nascerà una open all'altezza, Giorgio la adotterà.

**Fa davvero il caffè?**
Sì, con una vera macchina a capsule sulla schiena. E alla peggio, è una costosa macchinetta del caffè.

**Che caffè usa?**
Le capsule della macchina che scegli. Giorgio non è legato a nessuna marca di macchine o capsule.

**Le mani abili sono incluse?**
No. Sono un'opzione sperimentale, che diventerà affidabile con dati di teleoperazione (vedi obiettivo aggiuntivo a € 150.000).

**Devo usare Claude?**
No. Il planner è sostituibile; il Sistema 1 funziona senza alcun modello linguistico.

**Spedite all'estero?**
I kit (Face, zaino-caffè, Body Kit) sì, con spedizione calcolata a parte. Il Giorgio completo in UE; fuori UE da valutare caso per caso (normative locali).

**Cosa succede se la campagna non raggiunge l'obiettivo?**
Su Kickstarter nessuno viene addebitato. Noi continueremo, più lentamente.

---

## Il team

[da completare: nomi, foto, bio, esperienze precedenti in robotica e hardware, ruoli]

Giorgio è progettato in Italia. [da completare: sede, ragione sociale]

---

## Un'ultima cosa

Avremmo potuto fare un altro render perfetto di un robot che nessuno può comprare. Abbiamo preferito un robot che puoi aprire con un cacciavite.

**Sostieni Giorgio.** Aiutaci a farlo uscire dal computer.

*E alla peggio, è una costosa macchinetta del caffè.*
