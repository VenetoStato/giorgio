# Kickstarter — Giorgio

Materiale pronto da incollare per la campagna Kickstarter di Giorgio (progetto v5, ottobre 2026).

| File | Contenuto |
|---|---|
| `campagna_IT.md` | Pagina campagna completa in italiano (titolo, sottotitolo, storia, parti open, sicurezza, specifiche, ricompense, budget, tabella di marcia, rischi, FAQ, stretch goal) |
| `campaign_EN.md` | Versione inglese della pagina |
| `video_script.md` | Script video 2:00 con shot list, tempi, voce IT + EN, titoli a schermo |
| `social_launch.md` | 5 post di lancio (LinkedIn IT ×2, X EN ×2, Instagram IT) + email pre-lancio IT/EN |

Immagini referenziate (da `../render/stills/`): `hero.png`, `exploded.png`, `coffee.png`, `logistics.png`, `face.png`, `safety.png`.

## Numeri chiave

- **Obiettivo:** 120.000 € (2 Giorgio fisici 56.200 · CE/sicurezza 18.000 · attrezzature 8.000 · dati mani 6.000 · team 20.000 · commissioni 9.600 · imprevisti 2.200)
- **Costo Giorgio completo:** ≈ 28.080 € → con 30% di margine sul prezzo 28.080 / 0,70 ≈ 40.100 €
- **Prezzi Giorgio completo (IVA esclusa):** Fondatori 39.900 € (5 pz, margine ≈ 29,6%) · Pioneer/listino 42.900 € (10 pz, margine ≈ 34,5%)
- **Ricompense:** 25 € Sostenitore · 49 € Kit digitale gusci · 149 € Giorgio Face · 1.190 € Zaino-caffè per OpenArm · 4.900 € Adotta Giorgio per una settimana (6) · 5.900 € Body Kit (20) · 8.500 € acconto Fondatori (5) · 5.000 € acconto Pioneer (10)

## Due vincoli di Kickstarter da risolvere PRIMA del lancio

1. **Prototipo funzionante obbligatorio, niente render fotorealistici.** Le regole per i progetti hardware/product design richiedono di mostrare un prototipo funzionante e vietano i render fotorealistici e la CGI che mostra funzioni non esistenti (disegni tecnici, CAD e schizzi sono ammessi). Una campagna basata solo sulla simulazione e sui render Blender verrebbe con ogni probabilità respinta in revisione.
   **Conseguenza:** serve almeno un prototipo fisico (anche P0, con parte delle funzioni) prima del lancio; i render in `../render/stills/` vanno sostituiti con foto reali o declassati a teaser fuori da Kickstarter. Le pagine contengono riquadri `[DA AGGIORNARE AL LANCIO]` per questo. In alternativa valutare un'altra piattaforma o una pre-campagna "Notify me" mentre si costruisce il P0 (verificare le regole della piattaforma scelta).
2. **Ricompensa massima 8.500 € per progetti con sede in Italia.** Per questo il Giorgio completo è strutturato come **acconto** (8.500 € Fondatori / 5.000 € Pioneer) con saldo tramite contratto separato, e il Body Kit è stato ridimensionato a 5.900 € (senza scanner/relè di sicurezza). **Verificare con il supporto Kickstarter** che il modello acconto + saldo fuori piattaforma sia accettato; se non lo è, togliere i tier di acconto e gestire le unità complete fuori da Kickstarter con lettere d'intenti.

## Checklist di ciò che manca

- [ ] **Prototipo fisico** funzionante + foto e video reali (sostituiscono `hero/exploded/coffee/logistics/face/safety.png`)
- [ ] Misure reali: altezza, massa totale, autonomia, velocità massima di lavoro (segnaposto nella tabella specifiche)
- [ ] **Bio del team**, foto, ruoli, esperienza hardware (sezione "Il team" e ultimo rischio)
- [ ] **Soggetto giuridico**: decidere se lanciare come persona fisica o come azienda (le unità complete e i piloti sono B2B → serve una società/partita IVA)
- [ ] Conto bancario italiano (IBAN) intestato al creatore/società; documenti d'identità e fiscali per la verifica
- [ ] **IVA**: le ricompense fino a 5.900 € sono indicate IVA inclusa; verificare con il commercialista IVA su vendite UE a privati (OSS) e su acconti B2B
- [ ] Termini legali per acconti, recesso e consegna come "piattaforma di sviluppo" senza marcatura CE (segnati `[termini da validare con un legale]`)
- [ ] Preventivi reali: consulente CE / valutazione dei rischi, gusci SLS in piccola serie, tempi di consegna OpenArm (Enactic) e Tracer (AgileX)
- [ ] Licenze open definitive per gusci/volto/software (proposte: CERN-OHL-W 2.0 e Apache-2.0) e repository pubblico
- [ ] Verifica licenza LEAP Hand (CAD solo uso non commerciale) prima di offrirla in qualsiasi kit
- [ ] Revisione marchi: macchina del caffè generica (nessuna marca); Generative Bionics/GENE.01 citati solo a confronto con disclaimer di non affiliazione
- [ ] Costi di spedizione per Face kit, zaino-caffè e Body Kit (UE / extra UE)
- [ ] Pagina pre-lancio "Notify me" + lista email
- [ ] Montaggio video secondo `video_script.md` (versione Kickstarter solo con riprese reali)

## Requisiti Kickstarter per creatori in Italia (verificati ottobre 2026)

- L'Italia è tra i paesi supportati.
- Persona fisica: maggiorenne (18+), residente in Italia, documento d'identità rilasciato dallo Stato (accettati anche documenti di altri paesi UE).
- Azienda: deve lanciare dal paese in cui è registrata; vanno dichiarati e verificati titolari effettivi e amministratori (documenti d'identità e fiscali).
- Conto corrente in Italia intestato alla persona/entità che raccoglie i fondi, che accetti accrediti in EUR (IBAN italiano).
- Commissioni: 5% Kickstarter + commissioni di pagamento (budget calcolato su ~8% complessivo).
- Ricompensa massima per progetti italiani: 8.500 €.

Fonti:
- [Who is eligible to use Kickstarter?](https://updates.kickstarter.com/who-is-eligible-to-use-kickstarter/)
- [Kickstarter eligibility 2026 (boostyourcampaign)](https://www.boostyourcampaign.com/blog/kickstarter-eligibility)
- [Is there a maximum reward tier value? (Kickstarter Help)](https://help.kickstarter.com/hc/en-us/articles/115005128334-Is-there-a-maximum-reward-tier-value)
- [What are the rules for hardware and product design projects? (Kickstarter Help)](https://help.kickstarter.com/hc/en-us/articles/115005134554-What-are-the-rules-for-hardware-and-product-design-projects)
- [Kickstarter Is Not a Store](https://www.kickstarter.com/blog/kickstarter-is-not-a-store)
