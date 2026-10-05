# Giorgio launch plan (draft, 2026-10-05) — nothing is posted without the owner's explicit OK

Videos: `~/Videos/Giorgio/v19_serie/` (teaser 68 s, componenti 57 s, attivita 51 s, training 68 s, personalizza 66 s, lungo 4:05).

**Gate before any post:** the GitHub repo `VenetoStato/giorgio` must be public, licensed, and contain `amr/`. The teaser says
"Fork it. Improve it. Send a pull request." Today the repo is private, has no licence, and has uncommitted work.

## Schedule (Europe/Rome)
| When | Where | What |
|---|---|---|
| Mon 5 Oct, 20:30–21:30 | YouTube | Long video (public) + teaser as a separate video. Shorts only if a 9:16 version exists |
| Mon 5 Oct, 21:00 | Reddit r/robotics | Teaser upload or YouTube link + text post (below) |
| Tue 6 Oct, 08:30 | LinkedIn (personal profile) | Teaser native upload + post IT (below) |
| Tue 6 Oct, 15:30 | Reddit r/ROS, r/reinforcementlearning; Hacker News "Show HN" | Link to the repo + long video |
| Wed 7 Oct, 12:30 | LinkedIn | "componenti" video (own AMR, CE route), post EN |
| Thu 8 Oct, 08:30 | LinkedIn | "training" video: "learn to train robots" |

## YouTube
**Long video title:** Giorgio — an open, CE-certifiable Italian service robot (design + simulation)
**Teaser title:** Italy deserves its own robot. Not a Ferrari. A Fiat Panda. | Giorgio teaser
**Description:**
Giorgio is an open mobile bimanual service robot. It is designed in Italy to be simple, open and fixable, and to be certifiable
under the EU Machinery Regulation. It has two OpenArm 2.0 arms, 3D vision, and our own self-charging mobile base built from
certified safety components (SICK laser scanners, Pilz safety controller, ez-Wheel safety drives). It picks, sorts, carries
and serves coffee, and it learns new skills in simulation in about 90 minutes on one GPU.
Everything is open: CAD, electrical design, simulation, training code, parts list. → https://github.com/VenetoStato/giorgio
This is a design shown in simulation; the prototype is not built yet.
Ferrari is a trademark of Ferrari S.p.A.; Fiat and Panda are trademarks of FCA Italy S.p.A. (Stellantis), named only as a comparison. All other names are trademarks of their respective owners.
**Tags:** robotics, service robot, mobile manipulator, open source robot, reinforcement learning, MuJoCo, OpenArm, AMR, Made in Italy, CE marking
**Chapters (long video):** to be filled from the edit timeline (`render/edit_lungo.json`).

## Reddit (r/robotics, flair "Showcase"/"Project"; disclose it is our own project)
**Title:** I designed an open, CE-certifiable bimanual service robot (Italy) — full CAD, safety electrics and RL training are on GitHub
**Body:**
Hi all, this is Giorgio, our open mobile bimanual robot (still in simulation, prototype not built).
- Base: we couldn't find a commercial AMR with ≥85 kg payload, manufacturer-confirmed auto-docking and enough power out, so we designed our own from certified parts (SICK nanoScan3, Pilz PNOZmulti 2, ez-Wheel SWD safety drives). Every component value is traced to the manufacturer's manual.
- Arms: OpenArm 2.0. Skills like opening drawers/doors were trained in sim (236 M steps, ~95 min on one GPU, 96–99 % success).
- Everything is open: CadQuery CAD, netlist and safety functions, MuJoCo sim, training code.
Feedback welcome, especially from people who have CE-marked a mobile manipulator. Repo: https://github.com/VenetoStato/giorgio

## LinkedIn (Tue 08:30, IT)
Abbiamo progettato un robot di servizio italiano: aperto, semplice, e pensato fin dall'inizio per la marcatura CE.

Giorgio non è una Ferrari. È una Fiat Panda: si capisce, si ripara, si migliora.

🔧 Base mobile nostra, costruita con componenti di sicurezza certificati (SICK, Pilz, ez-Wheel). Ogni dato viene dai manuali dei costruttori.
🧠 Le abilità le impara in simulazione: aprire cassetti e ante in circa 90 minuti su una GPU.
☕ Prende pezzi, smista, trasporta, e fa il caffè.
📂 Tutto è aperto su GitHub: CAD, schemi elettrici, simulazione, codice di training. Fate fork, proposte, critiche.

È ancora un progetto in simulazione: cerchiamo aziende pilota, integratori e chi vuole costruirlo con noi in Italia.
👉 github.com/VenetoStato/giorgio

#robotica #MadeInItaly #opensource #automazione #AI #manifattura

(Ferrari è un marchio di Ferrari S.p.A.; Fiat e Panda sono marchi di FCA Italy S.p.A. (Stellantis), citati solo come paragone.)

## Connections needed
- YouTube: a YouTube connector/MCP with upload scope on the owner's channel (or the owner uploads; I prepare files and texts).
- Reddit: a Reddit connector/MCP with submit scope (new accounts have karma limits in r/robotics; check the subreddit rules).
- LinkedIn: a LinkedIn connector/MCP with post scope, or LinkedIn's native scheduler (Post → clock icon → Tue 08:30).
- Scheduling: once a connector exists, a scheduled cloud routine (`/schedule`) can publish at the set time; each post's final text is approved by the owner first.
