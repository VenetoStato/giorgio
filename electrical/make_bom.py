#!/usr/bin/env python3
"""Consolidated Giorgio bill of materials -> docs/BOM.md + docs/bom.csv

Merges, without double counting:
  1. cad/out/bom_parts.csv      (every CAD part: custom, shell, purchased, fastener-type T-nuts/pins)
  2. cad/out/bom_fasteners.csv  (screws per joint group)
  3. electrical/netlist.yaml    (power, protection, safety, dock)
  4. FEASIBILITY.md section 5   (part swaps: Insta360 -> UVC fisheyes, PCAN-USB FD, Pilz ES ETH, switch, face, coffee MCU)
  5. README.md v7 BOM           (prices of the big purchased subsystems)

De-duplication rule: every physical item has exactly ONE owner line.
  * Electrical/safety parts that also appear in the CAD (battery, DC-DCs, PNOZ, contactors, Tracer charger, scanners,
    RoboPad collector) are priced from netlist.yaml; the CAD row is mapped to that line (column 'dedup').
  * Big subsystems in the CAD (base, OpenArm torso body_link0, Jetson, Gemini, coffee machine) are priced once in the
    subsystem section; CAD rows are mapped.
  * Swapped-out parts (Insta360 X4 and its mast) are listed in 'removed' and not summed.
  * netlist 'load' placeholders (price 0) are ignored.
Usage: python3 make_bom.py   (Python 3 + PyYAML)
"""
import csv
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOCS = ROOT / "docs"
NET = yaml.safe_load((HERE / "netlist.yaml").read_text())
COMP = {c["id"]: c for c in NET["components"]}
BASE = yaml.safe_load((HERE / "base_choice.yaml").read_text())

lines = []          # dict(section, item, mpn, qty, unit, source, config, note)
mapped = []         # (cad part, owner line)
removed = []        # (item, reason)


def add(section, item, qty, unit, source, mpn="", note="", config="all"):
    lines.append(dict(section=section, item=item, mpn=mpn, qty=qty, unit=float(unit), source=source, note=note, config=config))


# ============================================================================ 1. subsystems (purchased)
S = "A. Mobile base"
for b in BASE["lines"]:
    add(S, b["item"], b.get("qty", 1), b["unit"], b["source"], b.get("mpn", ""), b.get("note", ""))

S = "B. Arms and end effectors"
add(S, "Enactic OpenArm 2.0 bimanual (2 arms, torso body_link0, 2 grippers, wrist cameras, 1 USB-CANFD) incl. shipping/duties", 1, 5950,
    "README v7 BOM (USD 6,000 by e-mail order + shipping/duties); https://docs.openarm.dev/purchase", "OpenArm 2.0 bimanual")

S = "C. Compute, perception, comms"
add(S, "NVIDIA Jetson AGX Orin 64 GB developer kit", 1, 3150, "README v7 BOM", "945-13730-0050-000 (dev kit)")
add(S, "Orbbec Gemini 336L stereo depth camera", 1, 340, "https://store.orbbec.com/products/gemini-336l (USD 379)", "Gemini 336L")
add(S, "USB UVC fisheye camera ~180 deg 1080p (front + back), replaces Insta360 X4", 2, 50, "estimate (FEASIBILITY.md section 3.7 option A)", "Arducam/e-con class")
add(S, "PEAK PCAN-USB FD (one CAN-FD bus per arm)", 2, 260, "https://www.esacademystore.eu/en/PCAN-USB-FD (FEASIBILITY.md section 5)", "IPEH-004022")
add(S, "3.3 V CAN transceiver module for Orin MTTCAN (BMS bus + spare)", 2, 40, "estimate (FEASIBILITY.md section 5: +600 incl. 2 PCAN)", "SN65HVD230 class")
add(S, "Industrial Ethernet switch 5-8 port, 24 V DIN (scanners, PNOZ, Jetson)", 1, 80, "estimate (FEASIBILITY.md section 5)")
add(S, "Powered USB 3 hub, 7 port, 12 V input", 1, 60, "estimate (FEASIBILITY.md section 6: 9-11 USB devices)")

S = "D. Face and UI"
add(S, "HUB75 32x16 P4 RGB LED panel", 1, 20, "estimate")
add(S, "ESP32-S3 HUB75 driver board (Matrix Portal S3 class)", 1, 25, "estimate (FEASIBILITY.md section 3.10)")
add(S, "GC9A01 1.28 in round displays (eyes)", 2, 6, "README v3/v7 (5-10 EUR each)")
add(S, "LED strips / mustache diffuser LEDs", 1, 15, "estimate (README v7 line 40 EUR incl. eyes)")

S = "E. Coffee backpack (barista)"
add(S, "24 V DC capsule machine, Nespresso-compatible, 300 W (truck type)", 1, 120, "https://www.truckstyler-shop.de/Suitable-for-Nespresso-Truck-24V-coffee-capsule-machine?slotID=2 (EUR 119.99)",
    note="CAD envelope is a De'Longhi Inissia EN80 (230 V); the electrical design requires the 24 V DC machine. CE / EN 60335-2-15 not stated by seller", config="barista")
add(S, "Actuonix P16-150-64-12-P linear actuator (cup shuttle)", 1, 95, "estimate (Actuonix list ~USD 100)", "P16-150-64-12-P", config="barista")
add(S, "HIWIN MGN12 rail L=190 + MGN12H carriage", 1, 45, "estimate", "MGN12-190 + MGN12H", config="barista")
add(S, "Coffee MCU: RP2040 + DRV8871 H-bridge + relay + cup-present sensor + 12 V buck", 1, 30, "FEASIBILITY.md section 5 (+30)", config="barista")
add(S, "Paper cups + capsules starter stock", 1, 0, "consumable, not counted", config="barista")

# ============================================================================ 2. electrical (netlist)
CAD_TO_NET = {"E01_battery_48V_40Ah_LFP": "PACK", "E02_dcdc_DDR480C_A": "DCDC_ARM", "E03_dcdc_DDR480C_B": "DCDC_ARM",
              "E05_pilz_PNOZ_mB0": "PNOZ", "E06_contactor_K1": "K_ARM", "E07_contactor_K2": "K_ARM",
              "E09_tracer_charger_48to24": "CHG_TRACER", "S02_nanoScan3_0": "SCANNER", "S02_nanoScan3_1": "SCANNER",
              "S03_roboteq_RPCOL90_100": "DOCK_CONTACTS"}
SEC_OF = {"battery": "F. Power", "fuse": "F. Power", "disconnect": "F. Power", "control": "F. Power", "protection": "F. Power",
          "dcdc": "F. Power", "charger": "F. Power", "contactor": "G. Safety", "relay": "F. Power", "resistor": "F. Power",
          "safety": "G. Safety", "connector": "F. Power", "wire": "H. Wiring and distribution", "distribution": "H. Wiring and distribution",
          "grounding": "H. Wiring and distribution", "emc": "H. Wiring and distribution", "interface": "C. Compute, perception, comms"}
BARISTA_ONLY = {"DCDC_COF", "K_COF", "FUSE_ATO20"}
for c in NET["components"]:
    if c["category"] == "load" or c.get("qty", 1) == 0:
        continue
    if c["id"] in BASE.get("drop_netlist", []):
        removed.append((c["mpn"], BASE.get("drop_reason", "not needed with the chosen base")))
        continue
    if c["id"] == "CHG_DOCK" or c["id"] == "DOCK_CONTACTS":
        sec = "J. Docking station"
    else:
        sec = SEC_OF[c["category"]]
    src = NET["sources"].get(c.get("source"), "") if c.get("source") else ""
    src = src or ("estimate" if c.get("assumed") else "netlist.yaml")
    if c.get("price_note"):
        src += " (" + c["price_note"] + ")"
    add(sec, c.get("desc") or c["mpn"], c.get("qty", 1), c.get("price_eur", 0), src, c["mpn"],
        "price estimate" if c.get("assumed") else "", "barista" if c["id"] in BARISTA_ONLY else "all")
add("G. Safety", "Pilz PNOZ m ES ETH (Modbus TCP status to Jetson)", 1, 400, "estimate (FEASIBILITY.md section 3.5)", "772134 (unverified)")
add("G. Safety", "Optocouplers 24 V -> 3.3 V for PNOZ status into Jetson GPIO", 1, 15, "estimate (FEASIBILITY.md section 6)")
add("F. Power", "DIN rail 35x7.5 + end stops (E04 in CAD)", 2, 6, "estimate", "EN 60715")
add("J. Docking station", "Station post / enclosure (Al profile + sheet), IP-rated charger mount, cable to wall socket", 1, 250, "estimate")
add("J. Docking station", "Station controller (ESP32), output relay 30 A DC, 12 V sense supply, Wi-Fi handshake", 1, 60, "estimate")
add("J. Docking station", "Docking target (AprilTag plate / laser ICP profile)", 1, 15, "estimate")

# ============================================================================ 3. CAD parts
PROC_MODEL = {   # (fixed EUR, EUR per kg) prototype qty 1, estimates
    "sheet": (20, 35), "plate": (80, 30), "mill": (180, 20), "weld": (350, 0), "turn": (12, 20), "pom": (6, 0),
    "sls_shell": (40, 220), "mjf": (10, 150), "epdm_sheet": (10, 0), "epdm_ext": (15, 20), "flatbar": (20, 0),
}
SUBSYS_MAP = {"tracer2_base": "A. Mobile base", "OA_body_link0": "B. OpenArm kit", "E08_jetson_agx_orin": "C. Jetson",
              "S05_orbbec_gemini_336L": "C. Gemini 336L", "S07_coffee_machine_inissia_EN80": "E. 24 V capsule machine",
              "S08_MGN12_rail_190": "E. MGN12", "S09_MGN12H_carriage": "E. MGN12", "S10_actuonix_P16_150": "E. Actuonix",
              "S10b_actuonix_rod": "E. Actuonix", "E04_din_rail_pnoz": "F. Power / DIN rail line"}
REMOVE = {"S04_insta360_X4": "replaced by 2 UVC fisheyes (FEASIBILITY.md section 5)",
          "P17_insta360_mast": "mast not needed once the Insta360 X4 is removed (fisheyes mount in the head shell)"}
COFFEE_PARTS = ("P21_", "P22_", "P23_", "P24_", "P25_", "P26_", "SH06_")


def cost_custom(row):
    proc = row["process"].lower()
    m = float(row["mass_kg"])
    name = row["part"]
    if name.startswith("P01"):
        return 80 + 30 * m + 150, "waterjet 10 mm 6082 + CNC drill/tap (~60 holes)"
    if "weld" in proc:
        return PROC_MODEL["weld"][0], "TIG weldment + post-machining"
    if "cnc milled" in proc:
        k = PROC_MODEL["mill"]
    elif "waterjet" in proc:
        k = PROC_MODEL["plate"]
    elif "turned" in proc:
        k = PROC_MODEL["turn"]
    elif "pom" in proc:
        k = PROC_MODEL["pom"]
    elif "sls" in proc and row["category"] == "shell":
        k = PROC_MODEL["sls_shell"]
    elif "mjf" in proc or "sls" in proc:
        k = PROC_MODEL["mjf"]
    elif "die-cut" in proc:
        k = PROC_MODEL["epdm_sheet"]
    elif "extruded" in proc:
        k = PROC_MODEL["epdm_ext"]
    elif "flat bar" in proc:
        k = PROC_MODEL["flatbar"]
    elif "laser" in proc or "sheet" in proc:
        k = PROC_MODEL["sheet"]
    else:
        raise ValueError(f"no cost model for {name}: {proc}")
    return k[0] + k[1] * m, row["process"]


groups = defaultdict(lambda: [0, 0.0, "", ""])
with open(ROOT / "cad/out/bom_parts.csv") as f:
    for row in csv.DictReader(f):
        name = row["part"]
        if name in REMOVE:
            removed.append((name, REMOVE[name]))
            continue
        if name in CAD_TO_NET:
            mapped.append((name, "netlist " + CAD_TO_NET[name]))
            continue
        if name in SUBSYS_MAP:
            mapped.append((name, SUBSYS_MAP[name]))
            continue
        if name in BASE.get("drop_cad", []):
            removed.append((name, BASE.get("drop_reason", "base change")))
            continue
        cfg = "barista" if name.startswith(COFFEE_PARTS) else "all"
        if row["category"] in ("custom", "shell"):
            unit, how = cost_custom(row)
            sec = "I. Shells (SLS/MJF PA12, painted)" if row["category"] == "shell" else "K. Structure (custom parts)"
            add(sec, f"{name} ({row['material']}, {row['mass_kg']} kg)", 1, round(unit, 0), "estimate: process cost model", "", how, cfg)
        elif row["category"] == "fastener":
            key = row["process"].replace("purchased ", "")
            g = groups[key]
            g[0] += 1
            g[2] = cfg if g[2] in ("", cfg) else "all"
        elif row["category"] == "purchased":
            if name.startswith("S01_"):
                add("K. Structure (custom parts)", "item Profil 8 80x80 leicht 0.0.265.80 cut 370 mm + machining", 1, 60,
                    "estimate (item price ~25 EUR/m + cut/drill/tap)", "item 0.0.265.80")
            else:
                raise ValueError("unmapped purchased CAD part " + name)
        else:
            raise ValueError(name)
FPRICE = {"T-slot nut slot 6 M5": 0.9, "T-slot nut slot 8 M6": 1.0, "ISO 7379 shoulder screw D8x8 M6": 3.0}
for key, (n, _, cfg, _) in groups.items():
    unit = next((v for k, v in FPRICE.items() if key.startswith(k)), 1.0)
    add("L. Fasteners and hardware", key, n, unit, "estimate", "", "", cfg or "all")

SCREW = {"M3": 0.08, "M4": 0.10, "M5": 0.13, "M6": 0.16, "M8": 0.30, "M12": 0.90}
with open(ROOT / "cad/out/bom_fasteners.csv") as f:
    agg = defaultdict(int)
    extras = defaultdict(int)
    for row in csv.DictReader(f):
        q = int(row["qty"])
        agg[(row["fastener"], row["grade"])] += q
        w = row["with"]
        if "washer" in w:
            extras["ISO 7089 washer 200HV"] += q
        if "Kerb Konus 860" in w:
            extras["Kerb Konus 860 M4 insert"] += q
        if "ISO 4032" in w:
            extras["ISO 4032 M5 nut 8"] += q
for (fs, gr), q in sorted(agg.items()):
    size = fs.split()[2].split("x")[0]
    add("L. Fasteners and hardware", f"{fs} {gr}", q, SCREW[size], "estimate (A2/8.8 catalogue price)")
add("L. Fasteners and hardware", "ISO 7089 washers (all sizes)", extras["ISO 7089 washer 200HV"], 0.03, "estimate")
add("L. Fasteners and hardware", "Kerb Konus 860 M4 threaded inserts", extras["Kerb Konus 860 M4 insert"], 1.2, "estimate")
add("L. Fasteners and hardware", "ISO 4032 M5 nuts", extras["ISO 4032 M5 nut 8"], 0.05, "estimate")
add("L. Fasteners and hardware", "Minimum-pack overhead, threadlocker, cable ties, glands", 1, 40, "estimate")

# ============================================================================ output
for l in lines:
    l["total"] = l["qty"] * l["unit"]
SECTIONS = sorted({l["section"] for l in lines})
tot_all = sum(l["total"] for l in lines)
tot_barista_only = sum(l["total"] for l in lines if l["config"] == "barista")
LABOUR_H, LABOUR_RATE = 35, 50

DOCS.mkdir(exist_ok=True)
with open(DOCS / "bom.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["section", "item", "mpn", "qty", "unit_eur", "total_eur", "config", "source", "note"])
    for s in SECTIONS:
        for l in lines:
            if l["section"] == s:
                w.writerow([s, l["item"], l["mpn"], l["qty"], f"{l['unit']:.2f}", f"{l['total']:.2f}", l["config"], l["source"], l["note"]])
    w.writerow(["TOTAL", "sum of parts, barista configuration (no margin, no labour)", "", "", "", f"{tot_all:.2f}", "barista", "", ""])
    w.writerow(["OPTIONAL", f"assembly + test labour {LABOUR_H} h x {LABOUR_RATE} EUR/h", "", LABOUR_H, f"{LABOUR_RATE:.2f}", f"{LABOUR_H * LABOUR_RATE:.2f}", "", "README v7", ""])

md = ["# Giorgio - consolidated bill of materials", "",
      f"Generated by `electrical/make_bom.py` on the current CAD export, netlist rev {NET['meta']['revision']} and base choice **{BASE['name']}**. "
      "Machine-readable copy: `docs/bom.csv`. EUR excluding VAT, prototype quantity 1. Prices marked *estimate* are not quotes.", "",
      "## Totals", "",
      "| | EUR |", "|---|---|",
      f"| **Sum of parts, barista configuration (default)** - no margin, no labour | **{tot_all:,.0f}** |",
      f"| of which barista-only items (coffee backpack, coffee DC-DC/relay/fuse, backpack structure) | {tot_barista_only:,.0f} |",
      f"| Optional: assembly and test labour, {LABOUR_H} h x {LABOUR_RATE} EUR/h (README v7) | {LABOUR_H * LABOUR_RATE:,.0f} |", ""]
md += ["## Subtotals by section", "", "| Section | EUR |", "|---|---|"]
for s in SECTIONS:
    md.append(f"| {s} | {sum(l['total'] for l in lines if l['section'] == s):,.0f} |")
md += ["", "## Configurations (deltas vs barista default)", "", "| Configuration | Delta EUR | What changes |", "|---|---|---|",
       f"| Logistics / kitting (no coffee) | {-tot_barista_only:,.0f} | remove all `barista` lines (backpack, 24 V machine, DDR-480C-24 coffee supply, K4, F6/F60) |",
       f"| Coffee brewed at the dock (option C) | {-tot_barista_only + 150:,.0f} | remove backpack; add a stock 230 V capsule machine in the station (~150) |"]
for d in BASE.get("config_deltas", []):
    md.append(f"| {d['name']} | {d.get('delta_text') or format(d['delta'], '+,.0f')} | {d['what']} |")
md += ["| 2x ORCA Hand v2 instead of grippers | +6,500 to +8,300 | FEASIBILITY.md; needs one DDR-120C-12 per hand (+100) |",
       "| 2x Pollen AmazingHand | +400 to +500 | FEASIBILITY.md; 5 V 2 A per hand from a DDR-60L-5 (+30) |",
       "| 2x RealSense D405 wrist upgrade | +540 | FEASIBILITY.md (estimate) |", ""]
md += ["## How double counting was avoided", "",
       "Every physical item has exactly one priced line. CAD rows that duplicate a priced line are mapped, not summed:", "",
       "| CAD part | Priced in |", "|---|---|"]
md += [f"| `{a}` | {b} |" for a, b in mapped]
md += ["", "Removed (not summed):", "", "| Item | Reason |", "|---|---|"]
md += [f"| {a} | {b} |" for a, b in removed]
md += ["", "- Electrical items exist once, in `electrical/netlist.yaml`. Its `load` placeholders (OpenArm, Jetson, Tracer) carry price 0 and are skipped.",
       "- The FEASIBILITY.md swaps are applied once:",
       "  - Insta360 X4 -> 2 UVC fisheyes",
       "  - +2 PCAN-USB FD + transceivers",
       "  - +PNOZ m ES ETH",
       "  - +Ethernet switch",
       "  - HUB75 face",
       "  - coffee MCU",
       "  - The 48 V pack, DC-DCs and charger are already in the netlist, so the FEASIBILITY '+1,500' lump is **not** added on top.",
       "- Custom-part prices use a per-process cost model (fixed + EUR/kg; see `make_bom.py` `PROC_MODEL`). These are prototype estimates, not quotes.", ""]
md += ["## Lines", "", "| Section | Item | MPN | Qty | Unit EUR | Total EUR | Config | Source |", "|---|---|---|---|---|---|---|---|"]
for s in SECTIONS:
    for l in lines:
        if l["section"] == s:
            src = l["source"] + (f" - {l['note']}" if l["note"] else "")
            md.append(f"| {s.split('. ')[0]} | {l['item']} | {l['mpn']} | {l['qty']} | {l['unit']:,.2f} | {l['total']:,.2f} | {l['config']} | {src} |")
md += ["", f"**Sum of parts (barista default): EUR {tot_all:,.0f}** (no margin, no labour). Optional labour: EUR {LABOUR_H * LABOUR_RATE:,.0f}.", ""]
(DOCS / "BOM.md").write_text("\n".join(md) + "\n")
print(f"lines {len(lines)}, mapped {len(mapped)}, removed {len(removed)}, total EUR {tot_all:,.0f} (barista-only {tot_barista_only:,.0f})")
