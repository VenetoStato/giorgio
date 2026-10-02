# Giorgio — alimentazione, ricarica automatica, sicurezza elettrica e certificazione

Stato: proposta di progetto (ottobre 2026). Fonti nelle due ricerche allegate in fondo; le voci "stima" non hanno fonte.

## 1. Fatto chiave

La base AgileX Tracer 2.0 **non può alimentare la sovrastruttura**: batteria 24 V 30 Ah LFP (720 Wh), presa accessori limitata a **5 A / 120 W** e staccata sotto soglia (manuale ufficiale). Bracci, calcolo e caffè hanno bisogno di **un pacco batteria dedicato**. AgileX non pubblica una stazione di ricarica per la Tracer (esiste per Ranger Mini 3.0 / Ranger Air: 24/48 V, 5–10 A, € 835) — da chiedere ad AgileX.

## 2. Bilancio di potenza

| Componente | Tensione | Tipico | Picco |
|---|---|---|---|
| 2 × OpenArm 2.0 (DM-J8009P spalla 20 A nom., DM-J4340/4310) | 24 V | 100–150 W | ~720 W (alimentatore 24 V 15 A per braccio) |
| Jetson AGX Orin | 19 V | 30–40 W | 60 W |
| 2 × SICK nanoScan3 | 24 V | 7,8 W | ~32 W |
| Pilz PNOZmulti 2 + contattori | 24 V | ~6 W | ~10 W |
| Orbbec Gemini 336L + Insta360 X4 | 5 V USB | ~7 W | ~20 W |
| Volto LED 32×16 P4 + striscia | 5 V | 2–4 W | 5–8 W |
| Trazione Tracer (95 kg, piano) — batteria propria | 24 V | 40–80 W | 800 W |
| Caffè: Nespresso Inissia (230 V) | inverter | ~20–25 Wh a tazzina | 1260 W (~1340 W lato DC) |
| Caffè: alternativa capsule 24 V DC | 24 V | ~ stesso Wh, piu' lento | ~300 W |

**Totale tipico senza caffè ≈ 250 W.** Picco teorico ≈ 3 kW → interlock software: niente erogazione mentre bracci o trazione lavorano.

## 3. Architettura consigliata (industrializzabile)

```
 STAZIONE (rete 230 V)                         ROBOT (tutto SELV ≤ 60 V DC)
 ┌───────────────────────────┐   contatti      ┌───────────────────────────────────────────────┐
 │ caricabatterie LFP 48 V    │==a molla 25 A==>│ pacco 48 V 40 Ah LFP (1,92 kWh ≤ 2 kWh)        │
 │ 25 A, CE (LVD+EMC)         │  attivi SOLO    │  BMS con CAN, IEC 62619 + UN 38.3, CE          │
 │ contatti alimentati solo   │  con robot      │   ├─ DC-DC 48→24 V 20 A (×2) ─► bus bracci 24 V │
 │ con robot agganciato       │  agganciato     │   │      (2 contattori DC in serie + precarica, │
 │ (rilevamento + CAN/IR)     │                 │   │       comandati dal PNOZ: arresto sicuro)   │
 └───────────────────────────┘                 │   ├─ DC-DC 48→24 V ─► scanner, PNOZ (sempre su) │
                                                │   ├─ DC-DC 48→19 V ─► Jetson                     │
                                                │   ├─ DC-DC 48→5 V  ─► camere, LED                │
                                                │   ├─ caricatore LFP 48→24 V 10 A ─► batteria     │
                                                │   │      Tracer (una sola coppia di contatti)    │
                                                │   └─ caffè: vedi decisione 2                    │
                                                └───────────────────────────────────────────────┘
```

- **Un solo punto di ricarica (48 V SELV)**: la stazione ricarica il pacco e, tramite caricatore a bordo, anche la batteria della Tracer.
- **Pacco ≤ 2 kWh**: evita passaporto batteria e due diligence del Reg. (UE) 2023/1542 per le batterie industriali > 2 kWh.
- **Arresto sicuro**: scanner → PNOZ (PL e) → contattori DC sul bus bracci + arresto della base. I motori Damiao non hanno STO e OpenArm non ha freni: prima un arresto controllato via CAN (categoria 1), poi il taglio di potenza; posa di sicurezza con bracci raccolti durante la navigazione.
- **Autonomia (stima)**: 1,92 kWh × 0,9 / ~250 W ≈ 6–7 h di lavoro, più la ricarica di opportunità alla stazione tra un compito e l'altro (25 A ≈ 1,2 kW: dal 30% all'80% in ~50 min).
- **Aggancio**: Nav2 `opennav_docking` (Apache-2.0) con ICP sul profilo laser della stazione o AprilTag; contatti a molla (es. Conductix-Wampfler Nano+, o piastre in ottone), stazione che alimenta i contatti solo a robot riconosciuto.

## 4. Certificazione: il percorso più breve

- **Regolamento Macchine (UE) 2023/1230** dal 20/01/2027: un robot mobile con bracci non è in Allegato I → **autocertificazione (modulo A)**, a patto che **nessuna funzione di sicurezza dipenda da IA/LLM**. Le funzioni di sicurezza restano hardware (scanner, PNOZ, contattori).
- **Norme**: EN ISO 12100 (rischi), EN ISO 3691-4 (base mobile), EN ISO 10218-1/-2:2025 (bracci, limiti PFL), ISO 13482 come riferimento per robot di servizio, EN ISO 13849-1 (PL d), EN 60204-1, IEC 62619 + UN 38.3 (batteria), EN 61000-6-1/-6-3 (EMC ambienti commerciali), RED + EN 18031 (Wi-Fi), AI Act art. 50 (dire a chi parla con Giorgio che è un'IA).
- **Dai fornitori**: dichiarazione di incorporazione della base (+ conformità ISO 3691-4), certificati PL di scanner e PNOZ, batteria marcata CE con IEC 62619/UN 38.3, caricabatterie CE.
- **Tempi (stima)**: con bracci già certificati e niente 230 V a bordo **6–9 mesi** al primo esemplare vendibile; con OpenArm e inverter a bordo **12–18 mesi**. Costi di consulenza e prove: **50–150 k€** (stima).

## 5. Decisioni aperte (le più importanti per i tempi)

1. **Bracci**: OpenArm (open, economico, ma va validato come parte della nostra macchina: monitoraggio forze PL d, arresto sicuro, prove PFL) oppure bracci cobot già certificati per la prima versione (es. UFactory xArm 6 ~9,5 k$ cad., Kinova Gen3, Doosan A0509, UR3e/UR5e).
2. **Caffè**: De'Longhi 230 V con inverter a bordo (allunga la certificazione) · macchina a capsule 24 V DC a bordo (SELV, più lenta) · caffè erogato solo alla stazione.
3. **Base**: Tracer 2.0 + pacco dedicato, oppure Ranger Mini 3.0 (48 V, stazione ufficiale, € 12,5k) — in entrambi i casi chiedere dichiarazione di incorporazione e conformità ISO 3691-4.

## 6. Verifiche in simulazione

`giorgio_v5.py` modella: consumi istantanei (bracci da coppia e velocità, ruote, elettronica, caffè), batteria di sistema, ricarica automatica sotto il 30%, divieto di caffè sotto il 20% se non agganciato, aggancio in anello chiuso con contatti fisici (molla 10 mm, tolleranze 20 mm / 3°). Banco di prova: `docktest` su 10 partenze casuali (batteria al 25%, ricarica automatica partita da sola).

**Risultato (2 ottobre 2026): 10 aggancio su 10, contatti chiusi.** Molla compressa 2,8–4,6 mm (finestra valida 0–10 mm), scarto laterale ≤ 2,0 mm (tolleranza 20 mm), angolo ≤ 0,28° (tolleranza 3°), tempo dalla partenza 21–27 s; in tutti i casi la carica sale (25,0% → 26,4% nel tempo accelerato del test).

Cosa è servito per arrivarci (e vale anche sul robot reale):
- **campo di protezione dedicato all'aggancio** (protezione 0,30 m, avviso 0,36 m): con i campi di marcia lo scanner vedeva la colonnina e rallentava fino a fermarsi 8,5 mm prima dei contatti;
- **colonnina 20 mm più indietro delle lamelle**: il paraurti la toccava prima che le molle si comprimessero;
- **conferma filtrata dei contatti**: stop solo dopo 10 letture consecutive di molla compressa (misura filtrata; rumore del riconoscimento 3 mm, 0,3°). Con una lettura singola un picco di rumore fermava il robot 4 mm prima del contatto.
- Sul robot reale lo stop si conferma anche con la **tensione presente sui contatti** (la stazione li alimenta solo dopo il riconoscimento).
