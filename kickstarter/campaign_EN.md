# Giorgio — Kickstarter campaign page (EN)

> **Title (54/60):** Giorgio: the open service robot that brings you coffee
>
> **Subtitle (109/135):** A mobile two-armed robot built from open, buyable parts. Logistics, vision, coffee — and it is yours to hack.
>
> **Category:** Technology → Robots · **Location:** Italy · **Currency:** EUR · **Duration:** 30 days · **Goal:** €120,000

> **[UPDATE BEFORE LAUNCH — PROTOTYPE STATUS]** Kickstarter requires a working prototype for hardware projects and does not allow photorealistic renderings. Before launch, replace every image marked "render" with photos and video of the physical prototype, and update this box with what the prototype actually does. See `README.md`.

![Giorgio — render/simulation, replace with prototype photo](../render/stills/hero.png)

---

## In short

**Giorgio is an open-hardware, mobile, two-armed service robot built from open and buyable parts.**
It drives from A to B among people and slows down when you come close. It inserts parts into a fixture, guided by vision. It makes you a coffee and puts it in your hand. You talk to it in plain language: *"Giorgio, make a coffee and bring it to Marco."*

It is not a closed humanoid that costs hundreds of thousands. It is a platform you can open, understand, repair and teach: **your open platform for your company's tasks.**

And worst case, it's a very expensive coffee machine.

**Where we are today, plainly:** everything on this page has been demonstrated **in physics simulation** (MuJoCo, with the vendors' official models). This campaign funds the first physical Giorgios, takes them out of the computer, and pays for the serious safety work.

---

## The story

Over the last two years, beautiful humanoid robots have appeared. Perfect videos, studio design, huge promises. Almost all of them share one thing: they are **closed**. You don't know what's inside, you can't repair them, you can't change a line of code, and often you can't even buy one.

Meanwhile, the open world moved fast. Enactic's **OpenArm 2.0** is a 7+7 DOF bimanual torso with QDD motors, hardware and software released under Apache-2.0. Mobile bases for logistics are mature products. Certified safety laser scanners come from a catalogue. Language models can turn a sentence into a plan.

So we asked: **what if we put together the best parts that already exist, and only added what's missing?** A beautiful body, a friendly face, safety done right, a brain that understands you. And a coffee machine on its back — because a robot that walks into an office first has to make itself liked.

That's how Giorgio was born. (Yes, he has a moustache.)

---

## What Giorgio is

![Exploded view of the parts — render, replace with photo/CAD](../render/stills/exploded.png)

Giorgio is four recognisable layers:

1. **Mobile base** — AgileX Tracer 2.0, a commercial differential-drive AMR (702 × 610 mm, 55 kg), ROS-supported.
2. **Safety** — two SICK nanoScan3 safety laser scanners and a Pilz PNOZmulti 2 safety relay: certified components, protective fields computed per ISO 13855.
3. **Torso and arms** — Enactic OpenArm 2.0 bimanual (7+7 DOF, Damiao QDD motors), with OpenArm parallel grippers and wrist cameras.
4. **Head and senses** — a round head with two round display eyes, a **backlit LED moustache** (our signature), an Orbbec Gemini 336L stereo RGB-D camera for manipulation, an Insta360 X4 360° camera on a short mast to see who's around, and an NVIDIA Jetson AGX Orin as the on-board brain.

On top: white satin soft-touch shells (painted SLS PA12), a dark-glass face and an orange accent. Studio-grade looks over a skeleton you can buy piece by piece.

![Giorgio's face — render, replace with photo](../render/stills/face.png)

**The eyes** are two round 1.28" GC9A01 displays. They look at the nearest person, blink, and change colour with the safety state:

| Eye colour | Meaning |
|---|---|
| Blue | all clear |
| Amber | slowing down (someone is in the warning field) — or *coffee mode* |
| Red | stopped (someone is in the protective field) |

A status LED strip around the base repeats the state, so you see it from behind too.

---

## What it does (in simulation, today)

### 1. Logistics among people

![Logistics with people — simulation](../render/stills/logistics.png)

Giorgio runs a logistics loop from A to B with smooth, jerk-limited driving: when braking, the torso pitches by about **0.4°** (suspended casters, modelled in simulation). When a person crosses its path, Giorgio **visibly slows down** in the warning field and **stops** in the protective field. Eyes go amber, then red. When the person leaves, it resumes.

### 2. Vision-guided insertion

At the workstation Giorgio uses the stereo camera to locate parts and insert them into a fixture: **8 out of 8 parts inserted**, with a vision error of about **1.6 mm**, in simulation.

### 3. Coffee, from cup to hand

![Coffee — render/simulation](../render/stills/coffee.png)

On Giorgio's back is a coffee backpack: a stock **commercial capsule machine** (brand-agnostic: any compact model with a button on top works), a stack of cups and a small linear-actuator shuttle on the flip-up cup support.

- the right arm takes a cup and places it on the shuttle;
- it presses the machine's button (we don't modify the machine — Giorgio uses it like you would);
- the shuttle brings the cup under the spout and back;
- the arm picks up the full cup, Giorgio drives to the person and **hands it over**.

While brewing, the eyes turn amber: *coffee mode*.

### 4. You talk, it plans

> *"Giorgio, make a coffee and bring it to Marco."*

Control works on two levels, like fast and slow thinking:

- **System 1 (fast):** a rule-based command and skill router answers simple commands ("stop", "go to station B") in **under 1 ms**. Works offline.
- **System 2 (deliberate):** a language-model planner (today Anthropic's Claude, via cloud API) turns complex sentences into a plan of skills:

```
fai_caffe → porta_caffe(Marco) → di("Here's your coffee, Marco!") → ricarica
```

Skills available today (names are Italian, of course): `vai_a` (go to), `fai_caffe` (make coffee), `porta_caffe` (deliver coffee), `carica` (load), `scarica_e_inserisci` (unload and insert), `ricarica` (recharge), `di` (say). When the battery runs low, Giorgio drives to its **charging dock** and docks by itself.

The planner never drives the motors directly and never touches safety: it only chooses **which skills** to run. The scanners and the safety relay are always on, independent of the software.

---

## What's open and what isn't (honestly)

We say "open" only where it truly is.

| Part | Component | Status |
|---|---|---|
| Arms + torso | Enactic OpenArm 2.0 (7+7 DOF) | **Open source** — hardware CERN-OHL-S-2.0, software Apache-2.0 |
| Grippers + wrist cameras | OpenArm 2.0 kit | **Open source** (part of OpenArm) |
| Motors | Damiao QDD | commercial (inside OpenArm) |
| Mobile base | AgileX Tracer 2.0 | **Commercial off-the-shelf**, ROS support — not open hardware |
| Safety scanners | 2× SICK nanoScan3 | commercial, certified |
| Safety relay | Pilz PNOZmulti 2 | commercial, certified |
| Manipulation vision | Orbbec Gemini 336L | commercial, public SDK |
| 360° vision | Insta360 X4 | commercial |
| Compute | NVIDIA Jetson AGX Orin | commercial |
| Coffee machine | compact capsule machine, brand of your choice | commercial, stock, unmodified |
| LLM planner | Claude (Anthropic), cloud API | commercial service, replaceable |
| **Shells, column, mounts, head** | Giorgio project | **Open** — CAD/STL released (proposed licence: CERN-OHL-W 2.0) |
| **Face: eyes + moustache + LEDs** | Giorgio project | **Open** — schematics and firmware (proposed: CERN-OHL-W 2.0 / Apache-2.0) |
| **Coffee backpack: shuttle + mounts** | Giorgio project | **Open** — CAD + firmware |
| **Software: skills, router, agent, simulation** | Giorgio project | **Open** — Apache-2.0 (proposed) |
| Dexterous hands (option) | ORCA Hand / Pollen AmazingHand | **Open, commercial use allowed**: ORCA CC BY 4.0 (software MIT), AmazingHand CC BY 4.0 (software Apache-2.0). Mounted and tested in simulation on gestures and buttons; grasps are taught. (LEAP and Aero Hand: non-commercial CAD, excluded.) |

In short: **everything we build ourselves is open.** What we buy, we buy from those who make it best — and we tell you.

---

## Safety: the boring part that matters most

![Safety fields — simulation](../render/stills/safety.png)

A robot that moves among people must know when to stop. We don't leave that to a neural network.

- **2× SICK nanoScan3** cover the base perimeter.
- **Pilz PNOZmulti 2** handles emergency stops and safety fields.
- **Speed-dependent fields per ISO 13855:** at standstill the protective field is **1.72 m**, computed with a human approach speed of 1.6 m/s (1,600 mm/s × 0.37 s + 1,128 mm). The faster Giorgio goes, the larger the fields.
- **Warning field → slow down. Protective field → stop.** Always, whatever the planner is thinking.
- Physical emergency-stop button on the robot.

**What Giorgio is NOT yet:** a certified machine. The safety components are certified, but **the integrated machine needs its own risk assessment and CE marking** under the EU Machinery Regulation 2023/1230 before it can be sold as a finished product in the EU. A large share of this campaign pays for exactly that work. Until then, Giorgio is a **development platform**, for use in controlled areas by trained staff.

---

## Why open

- **You can repair it.** Broken shell? Reprint it. Broken motor? It's a catalogue part.
- **You can understand it.** The code for skills, agent and simulation is right there.
- **You can teach it your job.** A company's tasks aren't the ones in a promo video. With an open platform, you write (or teach) the skills.
- **Nobody holds you hostage.** If we disappeared tomorrow, Giorgio would keep working: the parts are buyable, the files are public.

Giorgio is an alternative to the big closed humanoids — think of projects like Generative Bionics' GENE.01 — with a different choice: **no secret parts, only open and buyable parts, plus design work on top.** *(Generative Bionics and GENE.01 are mentioned for comparison only; no affiliation.)*

---

## Specs (design v5, October 2026)

| | |
|---|---|
| Arms | OpenArm 2.0 bimanual, 7+7 DOF, Damiao QDD |
| End effectors | OpenArm parallel grippers (default) |
| Dexterous hands | ORCA Hand / AmazingHand — **option**, grasps to be trained |
| Base | AgileX Tracer 2.0, differential drive, 702 × 610 mm, 55 kg (base only) |
| Overall footprint / height / mass | [to be measured on the prototype] |
| Safety | 2× SICK nanoScan3, Pilz PNOZmulti 2, e-stop; ISO 13855 fields (1.72 m protective at standstill) |
| Vision | Orbbec Gemini 336L (head), OpenArm wrist cameras, Insta360 X4 360° on mast |
| Compute | NVIDIA Jetson AGX Orin |
| Face | 2× round 1.28" GC9A01 displays, backlit LED moustache, status LED strip |
| Coffee | compact capsule machine (brand of your choice), linear-actuator shuttle, cup stack |
| Control | System 1 (router < 1 ms, offline) + System 2 (LLM planner, cloud) |
| Charging | automatic docking station |
| Runtime, max working speed | [to be defined with the prototype and the risk assessment] |
| Shells | SLS PA12, painted satin white soft-touch, dark-glass face, orange accent |
| Software | ROS-compatible, MuJoCo simulation included |

---

## What Giorgio costs, and why

Here are the numbers. Euros, excluding VAT.

| Item | € |
|---|---:|
| OpenArm 2.0 bimanual (grippers + wrist cameras, shipping/duties) | 5,950 |
| AgileX Tracer 2.0 | 7,500 |
| Orbbec Gemini 336L | 340 |
| Insta360 X4 | ~500 |
| NVIDIA Jetson AGX Orin | 3,150 |
| Safety: 2 scanners + PNOZ + e-stop | 4,800 |
| Tray, column, mounts | 500 |
| Painted SLS PA12 shells | 1,800 |
| Eyes + LEDs | 40 |
| Coffee backpack (capsule machine + shuttle actuator + cup holder) | ~250 |
| Charging dock | 900 |
| Cabling and power | 600 |
| Assembly and test (35 h) | 1,750 |
| **Total cost** | **≈ 28,080** |

With a 30% margin on price: **28,080 ÷ 0.70 ≈ €40,100**.

- **Founders early bird: €39,900 + VAT** (≈ 29.6% margin): a small discount for those who take the risk with us first.
- **Pioneer / list price: €42,900 + VAT** (≈ 34.5% margin): covers USD swings (OpenArm is priced in dollars), warranty and EU shipping.

---

## Rewards

> **Important Kickstarter note:** for Italy-based projects Kickstarter caps rewards at **€8,500**. That's why a complete Giorgio is reserved with a **deposit** on Kickstarter; the balance is settled under a separate contract before delivery. Reward amounts up to €5,900 include VAT; complete-Giorgio prices exclude VAT (business customers).

### €25 — Supporter
Your name engraved on the **back plate** of the first physical Giorgios, lab updates, high-res "moustache" wallpaper.
*Estimated delivery: December 2027 (photo of the plate).*

### €49 — Digital shell kit
**STL/CAD files of Giorgio's shells and mounts** with the full **build guide**, ahead of the public release, plus access to the builders' channel. (We'll release everything open anyway — here you pay to get it first and to support us.)
*Estimated delivery: May 2027 (shells v1) · final guide December 2027.*

### €149 — Giorgio Face
The **face kit**: two round 1.28" GC9A01 displays, controller board, backlit LED moustache with diffuser, cables. **Open firmware**, controllable over USB/ROS. The eyes track a point, blink and change colour. For your robot — or your desk. Shipping extra.
*Estimated delivery: September 2027.*

### €1,190 — Coffee backpack for OpenArm
For **OpenArm 2.0** owners: mount for a compact capsule machine (you pick the machine), linear-actuator shuttle with electronics, cup holder, mounting plate, open `fai_caffe` skill and calibration guide. Arm and base not included.
*Estimated delivery: December 2027.*

### €4,900 — Adopt Giorgio for a week (limited: 6)
A prototype Giorgio comes **to your company for 5 working days**, with one of our technicians, on an agreed task (internal logistics, coffee service in a controlled area). Includes site visit and site risk assessment. Northern and Central Italy; other areas on request. For businesses.
*Estimated window: March – June 2028.*

### €5,900 — Giorgio Body Kit (DIY, limited: 20)
All of **Giorgio's body except the parts you buy from others**: painted shells, column, tray and mounts, head with face kit, wiring harness, safety configuration files, software. **Does not include** OpenArm, Tracer 2.0, safety scanners/relay, Jetson, cameras or coffee machine — you get the exact shopping list.
*Estimated delivery: January 2028.*

### €8,500 — Giorgio Founders: deposit (limited: 5)
Reserve one of the **first 5 complete Giorgios** at the early-bird price of **€39,900 + VAT**. The €8,500 is a deposit deducted from the price; the balance (€31,400 + VAT) is settled under a separate contract before shipping. Includes one training day and your name on the plate.
*Estimated delivery: September 2028.*

### €5,000 — Giorgio Pioneer: deposit (limited: 10)
Reserve a **complete Giorgio** at **€42,900 + VAT**, with a €5,000 deposit deducted from the price and the balance (€37,900 + VAT) under a separate contract.
*Estimated delivery: December 2028.*

> A complete Giorgio ships as a **development platform** with the safety documentation available at that time. If CE marking of the integrated machine is not complete by delivery, we'll tell you before the balance is due and you can choose to wait or withdraw with a refund of the deposit (net of platform fees). [terms to be validated by a lawyer]

---

## Goal and use of funds — €120,000

| Item | € |
|---|---:|
| Two complete physical Giorgios (one for testing and CE assessment, one for pilots) | 56,200 |
| Risk assessment, safety-function validation, CE consulting (EU Reg. 2023/1230) | 18,000 |
| Tooling: small-series shell setup, assembly and painting jigs | 8,000 |
| Dexterous-hand data collection (teleoperation, one pair of hands) | 6,000 |
| Team: 6 months of integration and sim-to-real | 20,000 |
| Kickstarter and payment fees (~8%) | 9,600 |
| Contingency | 2,200 |
| **Total** | **120,000** |

Physical rewards (Face, coffee backpack, Body Kit, complete Giorgios) carry their own margin and don't eat into this budget.

---

## Stretch goals

- **€150,000 — Dexterous hands, for real.** We publish an open dataset of teleoperated demonstrations and trained policies for ORCA and AmazingHand on Giorgio's skills.
- **€200,000 — Motorised column.** Lifting-column option (400 mm stroke) to work from floor to counter.
- **€250,000 — "Reception" skill pack.** 360° people recognition and greeting, guest escort, object hand-off at reception.
- **€300,000 — A Giorgio for the community.** A third Giorgio loaned to an Italian university or makerspace, open to anyone who wants to develop skills.

---

## Timeline

| When | What |
|---|---|
| Oct 2026 (done) | Design v5 complete in simulation: A→B logistics, 8/8 vision insertion, coffee and hand-over, natural-language commands |
| Q4 2026 – Q1 2027 | [launch prerequisite] first physical prototype, real photos and video |
| Campaign launch | [date TBD] — 30 days |
| May 2027 | Digital shell kit v1 to backers |
| Q2 – Q3 2027 | OpenArm and Tracer orders for the two campaign Giorgios; assembly; driving tests in a controlled area |
| Sep 2027 | Giorgio Face ships |
| Q4 2027 | Safety-function validation; coffee backpack for OpenArm (Dec) |
| Jan 2028 | Body Kit ships |
| Q1 2028 | Risk assessment and CE technical file |
| Mar – Jun 2028 | Company pilot weeks |
| Sep 2028 | Founders Giorgios delivered |
| Dec 2028 | Pioneer Giorgios delivered |

---

## Risks and challenges

Here's where things can go wrong.

- **Simulation ≠ reality.** The results on this page come from an accurate physics simulation with the vendors' official models. But reality has friction, cables, lighting, dirty floors. We expect weeks of tuning: vision error, grasping, braking, docking. We've budgeted time for it, and we'll report it in updates — including when it doesn't go well.
- **Dexterous hands.** Open articulated hands (ORCA, AmazingHand) can be mounted, but **scripted grasps are not reliable today**: they need teleoperation data and imitation learning. That's why the standard Giorgio uses parallel grippers. Hands are an experimental option, not a promise.
- **CE marking.** The risk assessment may require changes (lower speeds, larger fields, extra guarding). If marking takes longer, complete-Giorgio deliveries slip. We prefer it that way.
- **Supply of OpenArm and other parts.** OpenArm 2.0 is ordered from Enactic, with lead times and USD prices that can change; the same applies to Tracer, Jetson and scanners. We have margin for price swings, not for a supply crisis: in that case we'll delay and tell you immediately.
- **Cloud dependency.** The System 2 planner currently uses a language model via API: without network Giorgio still runs direct System 1 commands but can't plan complex sentences. We're evaluating local planners on the Jetson.
- **The coffee machine.** We use a stock, unmodified capsule machine in a way it wasn't designed for (a robot presses it): the manufacturer's warranty may not cover this use.
- **We're a small team.** [to be completed: team's hardware-building track record]

---

## FAQ

**Does Giorgio exist?**
The complete design exists and has been verified in physics simulation. [UPDATE AT LAUNCH: description of the physical prototype.] Campaign funds build the physical Giorgios and get them certified.

**Is it a humanoid?**
It has a torso, two 7-DOF arms, a head and a face. It moves on wheels, not legs: in offices and warehouses, wheels are safer, more efficient and cheaper.

**Can I use it at my company right away?**
As a development platform, in a controlled area with trained staff, yes. As a CE-marked machine for general use, not yet — that's one of the campaign's goals.

**Why not an open base?**
We haven't found a mature open one with the same reliability and ROS support. The Tracer 2.0 is commercial and we say so. If a good open one appears, Giorgio will adopt it.

**Does it really make coffee?**
Yes, with a real capsule machine on its back. And worst case, it's a very expensive coffee machine.

**Which coffee?**
Whatever capsules your machine takes. Giorgio isn't tied to any machine or capsule brand.

**Are dexterous hands included?**
No. They're an experimental option that will become reliable with teleoperation data (see the €150,000 stretch goal).

**Do I have to use Claude?**
No. The planner is replaceable; System 1 works without any language model.

**Do you ship internationally?**
Kits (Face, coffee backpack, Body Kit) yes, shipping charged separately. Complete Giorgios within the EU; outside the EU case by case (local regulations).

**What if the campaign doesn't reach its goal?**
On Kickstarter nobody is charged. We'll keep going, just slower.

---

## The team

[to be completed: names, photos, bios, previous robotics/hardware experience, roles]

Giorgio is designed in Italy. [to be completed: location, legal entity]

---

## One last thing

We could have made yet another perfect render of a robot nobody can buy. We chose to build a robot you can open with a screwdriver.

**Back Giorgio.** Help us take him out of the computer.

*And worst case, it's a very expensive coffee machine.*
