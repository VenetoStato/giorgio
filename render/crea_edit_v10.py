"""Montaggio v10 (inglese, stile tecnico/ironico): genera edit_v10.json. I segmenti _CAD/_ELEC si riempiono quando ci sono i materiali."""
import json, os
BLACK, WHITE, GREY, ACC = [6, 6, 8], [245, 245, 242], [150, 152, 158], [255, 122, 26]


def T(t0, t1, text, pos="ll", size=64, w="H", **k):
    d = dict(t0=t0, t1=t1, text=text, pos=pos, size=size, weight=w, align="left" if pos in ("ll", "kick", "left") else "center")
    d.update(k); return d


def kick(t0, t1, text, above=120):
    return T(t0, t1, text, "kick", 24, "X", color=ACC, shadow=False, band=False, above=above, track=2)


def card(dur, *texts, **k):
    d = dict(type="card", dur=dur, color=BLACK, texts=list(texts), xfade=0.2); d.update(k); return d


def big(t0, t1, text, size=96, **k):
    return T(t0, t1, text, "center", size, "H", color=WHITE, shadow=False, band=False, track=3, **k)


def mono(t0, t1, text, pos="sub2", size=26, **k):
    return T(t0, t1, text, pos, size, "X", color=GREY, shadow=False, band=False, track=1, **k)


def shot(glob, tag, *texts, **k):
    d = dict(type="frames", glob=glob, tag=tag, texts=list(texts)); d.update(k); return d


S = []
# --- apertura
S.append(card(3.2, mono(0.2, 3.2, "GIORGIO // SERVICE ROBOT // REV.10", pos="upper", size=24), big(0.6, 3.2, "WE COULDN'T BUILD THE PARTS.")))
S.append(card(2.4, big(0.2, 2.4, "SO WE BOUGHT THEM.")))
S.append(card(3.4, big(0.2, 3.4, "AND HOPED THEY'D GET ALONG."), mono(1.4, 3.4, "(THEY MOSTLY DO.)")))
S.append(card(2.6, big(0.2, 2.6, "ITALY DESERVES ITS OWN ROBOT.", 84)))
S.append(card(2.2, big(0.2, 2.2, "NOT A FERRARI.", 96)))
S.append(card(3.6, big(0.2, 3.6, "MORE LIKE A FIAT PANDA.", 96), mono(1.0, 3.6, "CHEAP. OPEN. YOU CAN FIX IT YOURSELF.")))
S.append(card(3.8, big(0.2, 3.8, "ITALY ALSO HAS ITS OWN AI.", 84), mono(1.0, 3.8, "WE'VE SEEN THE MEMES.")))
S.append(card(3.6, big(0.2, 3.6, "GIORGIO'S AI ONLY PICKS SKILLS.", 80), mono(1.0, 3.6, "NO OPINIONS. NO HISTORY LESSONS.")))
S.append(shot("v10/h_hero/f_*.jpg", "RENDER", kick(0.5, 5.8, "MOBILE BIMANUAL SERVICE ROBOT"),
              T(0.5, 5.8, "GIORGIO.", size=110), T(1.6, 5.8, "Made entirely of other people's good ideas.", "llsub", 34, "N", band=False)))
S.append(shot("v10/h_face/f_*.jpg", "RENDER", kick(0.3, 5.8, "FACE"), T(0.3, 5.8, "32×16 RGB LED MATRIX", size=64),
              T(1.2, 5.8, "Expressions, attention, status. The moustache is non-negotiable.", "llsub", 32, "N", band=False)))
S.append(shot("v10/h_expl/f_*.jpg", "RENDER // EXPLODED", kick(0.3, 7.5, "BILL OF MATERIALS"), T(0.3, 7.5, "0% INVENTED HERE.", size=72),
              labels="lab_expl10.json", label_style="colonne", lab_t0=3.0,
              names={"testa": ["HEAD", "32×16 LED face · Insta360 X4 360° cam"], "braccio_sx": ["ARMS", "Enactic OpenArm 2.0 · open hardware"],
                     "braccio_dx": ["HANDS", "OpenArm gripper · ORCA · AmazingHand"], "busto": ["TORSO", "Orbbec Gemini 336L stereo depth"],
                     "vassoio": ["KITTING TRAY", "swappable chest module"], "caffe": ["COFFEE MODULE", "any capsule machine"],
                     "scanner": ["SAFETY", "2× SICK nanoScan3 · Pilz PNOZmulti"], "base": ["BASE", "AgileX Tracer 2.0 · commercial AMR"]}))
# --- configurazioni
S.append(card(2.8, big(0.2, 2.8, "ONE CHASSIS.\\nFOUR PERSONALITIES.".replace("\\n", "\n"), 84), mono(0.9, 2.8, "SAME BASE · SAME TORSO · SWAP HANDS AND BACKPACK")))
for f, a, b in (("cfg1_barista", "BARISTA", "Grippers + coffee module"), ("cfg2_logistica", "LOGISTICS", "Grippers + kitting tray"),
                ("cfg3_mani_orca", "DEXTEROUS", "2× ORCA Hand · open, tendon-driven"), ("cfg4_lowcost", "BUDGET", "2× AmazingHand · open, low-cost")):
    S.append(dict(type="card", dur=2.6, bg=f"stills_v10/{f}.png", dim=0.0, zoom=0.03, xfade=0.3,
                  texts=[T(0.15, 2.6, "CONFIGURATION", [1080, 690], 24, "X", color=ACC, shadow=False, band=False, track=2, align="left"),
                         T(0.15, 2.6, a, [1080, 730], 96, "H", color=WHITE, band=False, shadow=False, track=3, align="left"),
                         T(0.4, 2.6, b, [1084, 850], 34, "N", color=GREY, band=False, shadow=False, align="left")]))
# --- energia
S.append(card(2.6, big(0.2, 2.6, "POWER."), mono(0.8, 2.6, "48 V · ONE BATTERY · ONE PLUG")))
S.append(dict(type="frames", glob="v10/d_energia/f_*.jpg", ui=False))
S.append(dict(type="card", dur=5.5, bg="stills_v10/schema_elettrico.png", dim=0.0, zoom=0.10,
              texts=[kick(0.3, 5.5, "ELECTRICAL"), T(0.3, 5.5, "EVERY WIRE, FUSE AND\nCONTACTOR: SIZED AND CHECKED.".replace("\\n", "\n"), size=56)]))
S.append(shot("v10/b_xray/f_*.jpg", "RENDER // X-RAY", kick(0.3, 5.8, "INSIDE THE BASE"), T(0.3, 5.8, "BATTERY · DC-DC · SAFETY", size=60),
              labels="lab_base.json", label_style="colonne", lab_t0=1.0,
              names={"pw_battery": ["48 V LiFePO4", "1.92 kWh · BMS"], "pw_dcdc0": ["DC-DC", "48 V in · 24 / 19 / 5 V out"],
                     "pw_contactor": ["SAFETY CONTACTORS", "cut arm power on stop"], "pw_pnoz": ["SAFETY RELAY", "Pilz PNOZmulti"],
                     "pw_charger": ["24 V CHARGER", "keeps the base battery topped up"], "pw_jetson": ["COMPUTE", "NVIDIA Jetson AGX Orin"],
                     "charge_pad1": ["DOCK CONTACTS", "copper, spring-loaded"], "pw_tracer": ["AGILEX TRACER 2.0", "commercial AMR"]}))
S.append(shot("v10/r_wide/f_*.jpg", "SIM // 2×", kick(0.4, 6.5, "AUTO-DOCKING"), T(0.4, 6.5, "LOW BATTERY? IT GOES HOME.", size=60),
              battery=dict(json="ricarica_energia.json", src_step=2, travel_text="LOW · RETURNING TO DOCK", charging_text="DOCKED · CHARGING 48 V")))
S.append(shot("v10/r_close/f_*.jpg", "SIM", kick(0.3, 7.8, "DOCK"), T(0.3, 4.0, "CLOSED-LOOP DOCKING.", size=60),
              T(4.1, 7.8, "THE CONTACTS STAY DEAD\nUNTIL IT'S DOCKED.", size=60),
              battery=dict(json="ricarica_energia.json", src0=600, src_step=1, travel_text="LOW · RETURNING TO DOCK", charging_text="DOCKED · CHARGING 48 V")))
S.append(card(3.0, big(0.2, 3.0, "SAFETY LIVES IN HARDWARE.", 80), mono(0.9, 3.0, "NOT IN THE AI. HAVE YOU SEEN WHAT AI SAYS LATELY?")))
S.append(card(2.6, big(0.2, 2.6, "MECHANICAL."), mono(0.8, 2.6, "~100 PARTS · 128 BOLTED JOINTS · EVERY ONE CHECKED")))
S.append(shot("v10/k_cad/f_*.jpg", "CAD // CADQUERY", kick(0.4, 5.6, "ASSEMBLY"), T(0.4, 5.6, "REAL PARTS. REAL BOLTS.", size=60),
              T(1.2, 5.6, "Off-the-shelf where possible, laser-cut and printed where not.", "llsub", 32, "N", band=False)))
LINES = [("INTERFERENCE · EXACT B-REP · 3 POSES", "0 OVERLAPS"), ("BOLT AXES, MATING PARTS", "0.000 mm OFFSET"),
         ("HOLES · ISO 273 / TAP DRILLS / INSERTS", "OK"), ("THREAD ENGAGEMENT · EDGE DISTANCE", "OK"),
         ("ARM SWEEP vs STRUCTURE · 833 POSES", "3.1 mm MIN"), ("COFFEE SHUTTLE · 140 mm STROKE", "2.0 mm MIN"),
         ("TIPPING · NOMINAL", "6.7 m/s²"), ("MASS · ALL-IN", "146 kg"), ("OPEN ISSUES", "LISTED. HONESTLY.")]
tx = [T(0.2, 7.5, "VALIDATION REPORT", [160, 150], 26, "X", color=ACC, shadow=False, band=False, track=2, align="left")]
for i, (a, b) in enumerate(LINES):
    t0 = 0.5 + 0.45 * i; y = 230 + 72 * i
    tx.append(T(t0, 7.5, a + " " + "." * (44 - len(a)), [160, y], 34, "X", color=[200, 202, 206], shadow=False, band=False, align="left"))
    tx.append(T(t0 + 0.2, 7.5, b, [1240, y], 34, "X", color=WHITE if i < 8 else ACC, shadow=False, band=False, align="left"))
S.append(card(7.5, *tx))
# --- cosa fa
S.append(card(2.4, big(0.2, 2.4, "WHAT IT DOES.")))
S.append(shot("v10/l_carico/f_*.jpg", "SIM // 4×", kick(0.4, 4.8, "LOGISTICS"), T(0.4, 4.8, "LOADS ITSELF.", size=64),
              T(1.0, 4.8, "3D vision finds the parts. The arms plan around everything else.", "llsub", 32, "N", band=False)))
S.append(shot("v10/l_cross/f_*.jpg", "SIM", kick(0.3, 6.5, "SPEED & SEPARATION MONITORING"), T(0.3, 6.5, "SLOWS DOWN WHEN YOU'RE NEAR.\nSTOPS WHEN YOU'RE TOO NEAR.", size=54)))
S.append(shot("v10/l_drive/f_*.jpg", "SIM // 2×", kick(0.3, 5.0, "NAVIGATION"), T(0.3, 5.0, "A TO B. NO DRAMA.", size=64)))
S.append(shot("v10/l_ins/f_*.jpg", "SIM // 0.5×", kick(0.3, 5.6, "PRECISION"), T(0.3, 5.6, "VISION-GUIDED INSERTION.", size=60),
              T(1.0, 5.6, "Millimetre clearances. No jigs.", "llsub", 32, "N", band=False), slow=2))
S.append(shot("v10/l_oper/f_*.jpg", "SIM // 6×", kick(0.4, 7.5, "COLLABORATION"), T(0.4, 7.5, "WORKS NEXT TO PEOPLE.\nNOT INSTEAD OF THEM.", size=58)))
S.append(shot("v10/s_smista/f_*.jpg", "SIM // 4×", kick(0.4, 7.5, "SORTING"), T(0.4, 7.5, "SORTS BY COLOUR.", size=64),
              T(1.0, 7.5, "Without knocking over what it already sorted. (That took a while.)", "llsub", 32, "N", band=False)))
# --- software
S.append(dict(type="card", dur=4.6, bg="stills_v10/os_console.png", dim=0.0, zoom=0.04,
              texts=[T(0.3, 4.6, "GIORGIO-OS", [122, 975], 40, "H", color=WHITE, shadow=False, band=False, track=3, align="left"),
                     T(0.6, 4.6, "ONE CONSOLE. TALK TO IT, OR CLICK.", [470, 985], 26, "X", color=GREY, shadow=False, band=False, align="left")]))
S.append(dict(type="card", dur=4.2, bg="stills_v10/os_safety.png", dim=0.0, zoom=0.04,
              texts=[T(0.3, 4.2, "THE BIG RED BUTTON IS SOFTWARE. THE REAL ONE IS ON THE ROBOT.", [122, 985], 26, "X", color=GREY, shadow=False, band=False, align="left")]))
# --- mani RL
S.append(card(2.8, big(0.2, 2.8, "DEXTERITY IS TRAINED,\nNOT HAND-CODED.", 80)))
S.append(shot("v10/rlp2/f_*.jpg", "SIM // REINFORCEMENT LEARNING", kick(0.3, 4.3, "ORCA HAND · BEFORE"), T(0.3, 4.3, "UNTRAINED.", size=64)))
S.append(dict(type="card", dur=5.0, bg="stills_v10/rl_curva_dark.png", dim=0.0,
              texts=[mono(0.2, 5.0, "236 M SIMULATED ATTEMPTS · 4,096 PARALLEL ENVIRONMENTS · 81 MIN · ONE GPU", pos="upper", size=26)]))
S.append(shot("v10/rld2/f_*.jpg", "SIM // REINFORCEMENT LEARNING", kick(0.3, 9.8, "ORCA HAND · AFTER"), T(0.3, 5.0, "IN-HAND ROTATION, LEARNED.", size=60),
              T(5.1, 9.8, "NEXT: TEACHING IT\nTO A REAL HAND.", size=60)))
# --- caffe' (comico)
S.append(card(3.2, mono(0.2, 3.2, "AND NOW", pos="upper", size=26), big(0.5, 3.2, "THE MISSION-CRITICAL\nCAPABILITY.", 84)))
S.append(shot("v10/c_bicchiere/f_*.jpg", "SIM", kick(0.3, 5.3, "STEP 1"), T(0.3, 5.3, "CUP FROM STACK TO SHUTTLE.", size=60)))
S.append(shot("v10/c_eroga/f_*.jpg", "SIM // 3×", kick(0.2, 7.6, "STEPS 2–4"), T(0.2, 2.5, "START THE MACHINE.", size=60),
              T(0.6, 2.5, "Any capsule machine. We're not picky.", "llsub", 32, "N", band=False),
              T(2.6, 4.6, "SHUTTLE UNDER THE SPOUT.", size=60), T(4.7, 7.6, "ESPRESSO.", size=80)))
S.append(shot("v10/c_prende/f_*.jpg", "SIM", kick(0.3, 5.5, "STEP 5"), T(0.3, 5.5, "PICK UP THE FULL CUP.", size=60),
              T(1.0, 5.5, "Carefully. It's the most expensive cup in the building.", "llsub", 32, "N", band=False)))
S.append(shot("v10/c_consegna/f_*.jpg", "SIM // 2×", kick(0.3, 7.5, "STEP 6"), T(0.3, 3.4, "DELIVER.", size=72), T(3.5, 7.5, "ENJOY, MARCO.", size=72)))
S.append(dict(type="card", dur=5.0, bg="stills_v10/cfg1_barista.png", dim=0.15, zoom=0.05,
              texts=[T(0.5, 5.0, "WORST CASE,", [1300, 700], 80, "H", color=WHITE, shadow=False, band=False, track=3, align="left"),
                     T(1.5, 5.0, "IT'S A VERY EXPENSIVE\nCOFFEE MACHINE.", [1304, 800], 46, "N", color=WHITE, shadow=False, band=False, align="left")]))
S.append(card(3.0, big(0.2, 3.0, "IS IT OPEN?", 96), mono(1.2, 3.0, "YES. CAD, SCHEMATICS, CODE, BILL OF MATERIALS. ALL OF IT.")))
S.append(card(2.6, big(0.2, 1.3, "DID WE BUILD ONE?", 96), big(1.4, 2.6, "NO.", 140)))
S.append(card(5.0, big(0.2, 5.0, "SO DO US A FAVOUR.", 84), mono(1.0, 5.0, "BUILD ONE. TELL US WHAT BREAKS. WE'LL BUILD V2 FROM YOUR PROBLEMS.")))
BOM_TOTAL = open("bom_totale.txt").read().strip() if os.path.exists("bom_totale.txt") else "€[BOM]"
S.append(card(4.5, mono(0.2, 4.5, "BILL OF MATERIALS", pos="upper", size=26), big(0.4, 4.5, BOM_TOTAL + " IN PARTS.", 96),
              mono(1.2, 4.5, "SUM OF PARTS. NO MARGIN. ASSEMBLY NOT INCLUDED: THAT'S YOUR PART.")))
S.append(card(5.0, images=[dict(path="logo/logo_full_chiaro.png", t0=0.3, t1=5.0, pos=[960, 500], w=1100)]))
json.dump(dict(fps=30, size=[1920, 1080], music="music_v10.wav", xfade=0.45, ui=dict(head="GIORGIO // REV.10"), segments=S),
          open("edit_v10.json", "w"), ensure_ascii=False, indent=1)
print(len(S), "segmenti")
