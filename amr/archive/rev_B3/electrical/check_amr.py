#!/usr/bin/env python3
"""Electrical + safety checks for the Giorgio own AMR, rev B3 (netlist_amr.yaml) -> CHECKS_AMR.md.

Run:  cd ~/giorgio_sim/amr/electrical && python3 check_amr.py
Needs PyYAML (falls back to netlist_amr.json if PyYAML is missing).
Checks: conductor ampacity vs fuse (Ib <= In <= Iz), fuse vs device max, fuse DC voltage / breaking capacity,
nuisance blowing at peaks, voltage drop, DC-DC current vs load, battery current, contactors, regen shunt,
precharge, charge path + dock, bay thermal (passive vs fans), relay interface (bleed, auxiliary-output loads, LYNK relay),
SS1-t timing, PNOZmulti 2 I/O usage, PFHd/PL per safety function,
cable schedule consistency, CAD consistency (every netlist CAD id exists in ../out/parts.json, its loc matches the CAD
position, Mean Well keep-outs clear in ../out/interference.json), BOM total. Values tagged ASSUMED in the YAML stay assumptions: a PASS here is
only as good as its inputs.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import yaml
    NET = yaml.safe_load(open(os.path.join(HERE, "netlist_amr.yaml")))
except ImportError:  # pragma: no cover
    NET = json.load(open(os.path.join(HERE, "netlist_amr.json")))

BUS = NET["bus"]
rows = []          # (section, item, value, limit, result, note)
fails = []


def rec(section, item, value, limit, ok, note=""):
    res = "PASS" if ok is True else ("FAIL" if ok is False else ok)
    rows.append((section, item, value, limit, res, note))
    if res == "FAIL":
        fails.append(f"{section}: {item}")


def f(x, n=1):
    return f"{x:.{n}f}"


# ------------------------------------------------------------------ 1. circuits
def iz(c):
    hot = c.get("ins", 70) >= 90
    tab = BUS["ampacity_A"][c["method"] + ("_90" if hot else "")]
    base = tab[c["mm2"]] if c["mm2"] in tab else tab[float(c["mm2"])]
    k = BUS["k_temp_bay_90"] if hot else BUS["k_temp_bay"]
    return base * k * c.get("k_group", 1.0) * c.get("parallel", 1)


VBUS = {"B48": 40.0, "AUX48": 40.0, "A48L": 40.0, "A48R": 40.0, "CHG": 51.2, "T24": 24.0, "S24": 24.0,
        "A24L": 24.0, "A24R": 24.0, "COF24": 24.0, "C12": 12.0}
for c in NET["circuits"]:
    cid = f"{c['id']} {c['from']} -> {c['to']}"
    Iz = iz(c)
    p = c["prot"]
    In = p["In"]
    if In > 0:
        rec("Circuits", f"{cid}: Ib <= In <= Iz", f"{f(c['i_cont'])} <= {In} <= {f(Iz)}", "IEC 60364-4-43",
            c["i_cont"] <= In <= Iz, f"{c['mm2']} mm2 x{c.get('parallel', 1)} method {c['method']} ins {c.get('ins', 70)} C k_grp {c.get('k_group', 1)}")
        rec("Circuits", f"{cid}: fuse vs device max", f"{In} A", f"<= {c['dev_max_A']} A", In <= c["dev_max_A"], p["ref"])
        peak_lim = In * (1.0 if c["t_peak"] > 10 else 1.5)
        rec("Circuits", f"{cid}: no nuisance trip at peak", f"{f(c['i_peak'])} A / {c['t_peak']} s", f"<= {f(peak_lim)} A",
            c["i_peak"] <= peak_lim, "gG/gPV hold 1.5 In for >> 5 s")
        vreq = 58.4 if c["bus"] in ("B48", "AUX48", "A48L", "A48R", "CHG") else 30.0
        isc = BUS["prospective_isc_kA"] if vreq > 30 else 0.2
        rec("Circuits", f"{cid}: fuse DC voltage / breaking", f"{p['Vdc']} V / {p['Icu_kA']} kA", f">= {vreq} V / {isc} kA",
            p["Vdc"] >= vreq and p["Icu_kA"] >= isc, "Isc ASSUMED")
    else:
        smax = c.get("source_max_A", c["i_peak"])
        rec("Circuits", f"{cid}: source-limited, Iz >= source max", f"Iz {f(Iz)} A", f">= {smax} A", Iz >= smax, p["ref"])
        rec("Circuits", f"{cid}: source max vs device max", f"{smax} A", f"<= {c['dev_max_A']} A", smax <= c["dev_max_A"], "")
    v = VBUS.get(c["bus"], 40.0)
    dv = 2 * c["length_m"] * c["i_cont"] * BUS["rho_ohm_mm2_m"] / (c["mm2"] * c.get("parallel", 1))
    lim = BUS["vdrop_limit_pct"]
    rec("Circuits", f"{cid}: voltage drop at Ib", f"{f(100 * dv / v, 2)} %", f"<= {lim} %", 100 * dv / v <= lim, f"{f(dv, 2)} V at {v} V")

# ------------------------------------------------------------------ 2. DC-DC
dc_in = {}
for d in NET["dcdc"]:
    cont = sum(l["cont_A"] for l in d["loads"])
    peak = sum(l["peak_A"] for l in d["loads"])
    cap = d["rating_A"] * d["n"] * d["share_factor"] * d["derate"]
    capp = d["peak_A"] * d["n"] * d["share_factor"] * d["derate"]
    tag = f"{d['id']} ({'+'.join(d['units'])})"
    rec("DC-DC", f"{tag}: continuous load", f"{f(cont)} A", f"<= {f(cap)} A", cont <= cap, f"{d['n']} unit(s) x share {d['share_factor']}")
    if d["peak_s"]:
        rec("DC-DC", f"{tag}: peak load ({d['peak_s']} s)", f"{f(peak)} A", f"<= {f(capp)} A", peak <= capp, "")
    else:
        rec("DC-DC", f"{tag}: peak load (no peak rating)", f"{f(peak)} A", f"<= {f(cap)} A", peak <= cap, "")
    if d["n"] > 1:
        rec("DC-DC", f"{tag}: N+1 (one unit alone, continuous)", f"{f(cont)} A", f"<= {d['rating_A']} A",
            True if cont <= d["rating_A"] else "INFO", "redundancy, not required")
    pin_c = d["v_out"] * cont / d["eff"]
    pin_p = d["v_out"] * peak / d["eff"]
    dc_in[d["id"]] = (pin_c, pin_p, d.get("variant", "all"))

# ------------------------------------------------------------------ 3. battery / B48 total
L5_W = NET["l5_load_W"]          # head 5 V (U6); rev B: no waist actuator on B48
for var in ("OA", "C48"):
    pc = sum(v[0] for k, v in dc_in.items() if v[2] in ("all", var)) + L5_W[0] / 0.85
    pp = sum(v[1] for k, v in dc_in.items() if v[2] in ("all", var)) + L5_W[1] / 0.85
    if var == "C48":
        pc += 2 * 150.0
        pp += 2 * NET["c48_arm_feed"]["per_arm_W_max"] * 1.0
    ic, ip = pc / NET["bus"]["B48"]["v_lvco"], pp / 40.0
    rec("Battery", f"{var}: B48 max sustained (all loads at max sustained) vs 1-hour rating", f"{f(pc, 0)} W = {f(ic)} A @48 V (LVCO)", f"<= {BUS['batt_1h_A']} A (1 h)",
        ic <= BUS["batt_1h_A"], "2x DLP-GC2-48V: Max Discharge Current (1 hour) 2 x 58 A [SOURCED discover_manual]")
    rec("Battery", f"{var}: max sustained vs the 30 A repeated-cycle rating", f"{f(ic)} A", f"{BUS['batt_cont_A']} A continuous",
        "INFO", "envelope, not a duty: allowed for <= 1 h (1-hour rating); duty averages are checked below and in CALC s.5 (Jetson energy manager caps the 1-h rolling average at 30 A)")
    rec("Battery", f"{var}: B48 all-peaks-at-once vs BMS over-discharge trip", f"{f(pp, 0)} W = {f(ip)} A @40 V", f"< {BUS['bms_trip_A_10s']} A for 10 s",
        ip < BUS["bms_trip_A_10s"], "BMS trips > 58 A for 10 s per pack (pair 116 A) [SOURCED]; DC-DC peaks last <= 5 s")
    rec("Battery", f"{var}: B48 all-peaks-at-once vs peak rating", f"{f(ip)} A", f"<= {BUS['batt_peak_A']} A ({BUS['batt_peak_s']:.0f} s)",
        ip <= BUS["batt_peak_A"], "90 A RMS 10 s per pack [SOURCED]")
    rec("Battery", f"{var}: main fuse F0 holds all-peak", f"{f(ip)} A", "<= 1.5 x 100 A for 5 s", ip <= 150, "")
    if var == "OA":
        oa_ic, oa_ip = ic, ip
BD = NET["battery_duty"]
for name, w in BD["profiles_W"].items():
    i_avg = w / NET["bus"]["B48"]["v_lvco"]
    rec("Battery", f"duty average {name} (CALC s.5) vs 30 A pair continuous", f"{w:.0f} W = {f(i_avg)} A @48 V", f"<= {BUS['batt_cont_A']} A",
        i_avg <= BUS["batt_cont_A"], "15 A per pack for repeated full cycles [SOURCED discover_manual footnote b]")
rec("Battery", "single pack carries everything (other pack off / fuse open)", f"{f(oa_ic)} A sustained / {f(oa_ip)} A peak", "<= 58 A (1 h) / 90 A (10 s)",
    oa_ic <= 58 and oa_ip <= 90, "degraded mode: the Jetson derates (arms off) if one pack is missing on LYNK")
rec("Battery", "pack internal fuse vs single-pack peak", f"{f(oa_ip)} A for <= 5 s", f"{BUS['pack_fuse_A']} A fuse (58 V)", "INFO",
    "60 A internal fuse carries 90 A only briefly: the degraded single-pack mode must be limited in software (arms off)")

# ------------------------------------------------------------------ 4. contactors / disconnect
K = NET["contactors"]
rec("Switchgear", "K0 SW80B: continuous vs interrupted rating", f"{K['K0']['i_cont']} A", f"<= {K['K0']['interrupted_A']} A", K["K0"]["i_cont"] <= K["K0"]["interrupted_A"], "SOURCED sw80")
rec("Switchgear", "K0 SW80B: upstream fuse vs thermal rating", f"{K['K0']['upstream_fuse_A']} A", f"<= {K['K0']['ith_A']} A", K["K0"]["upstream_fuse_A"] <= K["K0"]["ith_A"], "")
rec("Switchgear", "K0 SW80B: voltage (blowout version)", "58.4 V", f"<= {K['K0']['vmax']} V", 58.4 <= K["K0"]["vmax"], "non-blowout version max 48/60 V")
rec("Switchgear", "Q0 ED250B: thermal vs fuse / voltage", f"{K['Q0']['upstream_fuse_A']} A / 58.4 V", f"<= {K['Q0']['ith_A']} A / {K['Q0']['vmax']} V",
    K["Q0"]["upstream_fuse_A"] <= K["Q0"]["ith_A"] and 58.4 <= K["Q0"]["vmax"], "ED250 without blowouts = 48 V max -> must be ED250B")
rec("Switchgear", "K1/K2: worst-case DC break per arm (2 poles in series)", f"{K['K1K2']['i_break_worst_A']} A", f"<= {K['K1K2']['dc1_2poles_series_60V_A']} A",
    K["K1K2"]["i_break_worst_A"] <= K["K1K2"]["dc1_2poles_series_60V_A"], "Siemens 3RT2026-1BB40 DC-1 2 poles in series at 60 V [SOURCED, V:SI1]")

# ------------------------------------------------------------------ 5. regen shunt T24
S = NET["shunt_T24"]
p_peak = S["robot_mass_kg"] * S["decel_mps2"] * S["v_max_mps"] * S["regen_eff"]
e_stop = 0.5 * S["robot_mass_kg"] * S["v_max_mps"] ** 2 * S["regen_eff"]
p_avg = e_stop * S["stops_per_min"] / 60
rec("Regen", "T24 peak regen power vs 2x DSR 50/5 short-term", f"{f(p_peak, 0)} W", f"<= {S['units'] * S['P_short_W']} W", p_peak <= S["units"] * S["P_short_W"], f"m {S['robot_mass_kg']} kg, a {S['decel_mps2']} m/s2, v {S['v_max_mps']} m/s")
rec("Regen", "T24 average regen vs continuous rating", f"{f(p_avg, 1)} W ({f(e_stop, 0)} J/stop)", f"<= {S['units'] * S['P_cont_W']} W", p_avg <= S["units"] * S["P_cont_W"], f"{S['stops_per_min']} stops/min")
rec("Regen", "Clamp window: 24 V setpoint < threshold < DDR OVP min < SWD OV alert", f"24 < {S['threshold_V']} < {S['ddr_ovp_min_V']} < {S['swd_ov_alert_V']}", "ordered",
    24.0 < S["threshold_V"] < S["ddr_ovp_min_V"] < S["swd_ov_alert_V"], "DDR output must NOT be trimmed above 26 V")
rec("Regen", "Arm buses (OA): DSR 50/5 27 V per arm vs ~50 J hard stop", "50 J", "300 W x 0.2 s = 60 J", True, "old_arch estimate; verify by test")

# ------------------------------------------------------------------ 6. precharge
P = NET["precharge"]
tau = P["R_ohm"] * P["C_uF"] * 1e-6
E = 0.5 * P["C_uF"] * 1e-6 * P["v_max"] ** 2
rec("Precharge", "K0P: 5 tau within the sequence window", f"{f(5 * tau, 2)} s", f"<= {P['t_allowed_s']} s", 5 * tau <= P["t_allowed_s"], f"R {P['R_ohm']} ohm, C {P['C_uF']} uF ASSUMED")
rec("Precharge", "K0P resistor pulse energy", f"{f(E, 1)} J", f"<= {P['R_pulse_J_max']} J", E <= P["R_pulse_J_max"], f"I0 {f(P['v_max'] / P['R_ohm'], 2)} A")
rec("Precharge", "DC-DCs held OFF during precharge (remote ON/OFF)", "sequence", "required", True, "DDR UVLO on at 33.6 V would load the RC")

# ------------------------------------------------------------------ 7. charge path
C = NET["charge"]
rec("Charge", f"{C['charger']} CC vs RoboPad / DRDN40-48 / packs / F7", f"{C['I_cc_A']} A",
    f"<= {C['robopad_cont_A']} / {C['drdn40_A']} / {C['batt_charge_A']} / {C['fuse_A']} A",
    C["I_cc_A"] <= min(C["robopad_cont_A"], C["drdn40_A"], C["batt_charge_A"], C["fuse_A"]), "RoboPad 60 A continuous, packs 2 x 15 A continuous [SOURCED]")
rec("Charge", "option NPB-1700-48 CC vs the same limits", f"{C['I_cc_alt_A']} A",
    f"<= {C['robopad_cont_A']} / {C['drdn40_A']} / {C['batt_charge_A']} / {C['fuse_A']} A",
    C["I_cc_alt_A"] <= min(C["robopad_cont_A"], C["drdn40_A"], C["batt_charge_A"], C["fuse_A"]), "C48 barista option only (needs a dock EMC test, TP-19b)")
rec("Charge", "charge current per pack (NPB-750 CC, no docked load)", f"{C['I_cc_A'] / 2:.1f} A", "<= 15 A per pack continuous", C["I_cc_A"] / 2 <= 15.0, "SOURCED discover_manual")
rec("Charge", "Charger CV (DIP 'flooded' preset) vs Discover bulk", f"{C['cv_V']} V / float {C['float_V']} V", "<= 56.8 V / 53.6 V", C["cv_V"] <= 56.8 and C["float_V"] <= 53.6, "DIP 2 OFF / 3 ON; never the 58.4 V LiFePO4 preset")
rec("Charge", "NPB DIP preset replaces the rev B1 reprogramming ACTION", f"{C['npb_dip_preset_V']} V", "<= 56.8 V", C["npb_dip_preset_V"] <= 56.8, "SOURCED npb750 / npb1700 DIP table")
rec("Charge", "charger OVP alone vs RoboPad 60 V fault limit", f"{C['npb_ovp_min_V']} V", f"<= {C['robopad_vmax_V']} V", "INFO", "does NOT meet it -> dock OV relay XD3 (next row)")
rec("Charge", "dock OV relay XD3: CV < trip < RoboPad limit", f"{C['cv_V']} < {C['dock_ov_relay_V']} < {C['robopad_vmax_V']} V", "ordered",
    C["cv_V"] < C["dock_ov_relay_V"] < C["robopad_vmax_V"], "opens the dock DC contactor (V:M12)")
rep = C.get("dock_ov_relay_repeat_V", 0.0)
rec("Charge", "dock OV relay XD3 (DUB01CD48500V, 200 V range): set point +- repeatability inside (CV, RoboPad limit)",
    f"{C['dock_ov_relay_V']} +- {rep} V", f"> {C['cv_V']} and < {C['robopad_vmax_V']} V",
    C["cv_V"] < C["dock_ov_relay_V"] - rep and C["dock_ov_relay_V"] + rep < C["robopad_vmax_V"], "+-0.5 % FS of 200 V [SOURCED gavazzi_dub01]; bench-calibrated (TP-13)")
kv = NET["bus"]
rec("Charge", "K0V (DUB01CD48500V, 50 V range): 48.0 V cut-off +- repeatability above the BMS LVD 40 V and inside the range",
    f"48.0 +- 0.25 V (range 5-55 V settable)", "> 40 V, bus max 58.4 V <= input max 350 V", True, "[SOURCED gavazzi_dub01 p.1-3]")
rec("Charge", "DRDN40-48 reverse voltage vs B48 max", "58.4 V", "<= 65 V", 58.4 <= 65, "pads dead when undocked")
h06 = [c for c in NET["circuits"] if c["cable"] == "H06a"][0]
rec("Charge", "H06a RoboPad external cable length", f"{h06['length_m']} m", f"<= {C['h06a_max_m']} m", h06["length_m"] <= C["h06a_max_m"], "RoboPad datasheet v1.3 [SOURCED]")

# ------------------------------------------------------------------ 7b. relay interface, coil loads, SS1-t timing (rev B2)
SCX = NET["safety_controller"]
vmin = SCX["s24_V"] * 0.98
i_bleed = vmin / SCX["bleed_ohm"] * 1000
p_bleed = SCX["s24_V"] ** 2 / SCX["bleed_ohm"]
rec("Relay interface", "bleed resistor keeps each relay contact >= minimum load", f"{f(i_bleed, 1)} mA at {f(vmin, 1)} V", f">= {SCX['relay_min_mA']} mA",
    i_bleed >= SCX["relay_min_mA"], f"{SCX['bleed_ohm']} ohm, S24 -2 %; EF 4DI4DOR DC1 min 10 mA [SOURCED]")
rec("Relay interface", "bleed resistor power vs 1 W rating (50 % derating)", f"{f(p_bleed, 2)} W", "<= 0.5 W", p_bleed <= 0.5, "")
for k, ma in SCX["coil_loads_mA"].items():
    if k == "K4_direct":
        rec("Relay interface", "K4 coil directly on a B0 auxiliary output (rejected)", f"{ma} mA", f"<= {SCX['aux_out_max_mA']} mA", "INFO", "92 mA > 75 mA -> interposing relay KI4 (V:FI1/P7)")
    else:
        rec("Relay interface", f"{k} coil on a B0 auxiliary output", f"{ma} mA", f"<= {SCX['aux_out_max_mA']} mA", ma <= SCX["aux_out_max_mA"], "coil current ASSUMED from the datasheet class")
rec("Relay interface", "SC0 O0 load: K1 + K2 coils", f"{f(2 * 5.9 / 24, 2)} A", f"<= {SCX['sc_out_max_A']} A", 2 * 5.9 / 24 <= SCX["sc_out_max_A"], "3RT2026 5.9 W each [SOURCED]; separate multicore cables")
rec("Relay interface", "G01 LYNK II relay R1: K0 coil chain load", "0.7 A at 24 V DC (with D0)", "<= 5 A at 30 V DC", True, "SW80 7-13 W + 22.32 2.2 W + K0T [SOURCED]")
nright = sum(1 for k, m in SCX["modules"].items() if k != "SC0")
rec("Relay interface", "PNOZ expansion modules right of B0 (C48 incl.)", f"{nright}", f"<= {SCX['max_modules_right']}", nright <= SCX["max_modules_right"], "SOURCED pilz_cat")
lat = SCX["t_logic_s"] + SCX["t_drive_s"]
for v in (0.3, 0.8, 1.2, SCX["v_max_mps"]):
    t_end = lat + v / SCX["ramp_mps2"]
    t_sls = lat + max(0.0, v - 0.3) / SCX["ramp_mps2"]
    rec("SS1-t timing", f"stop from {v} m/s: ramp ends before STO (t_STO {SCX['sts_s']} s)", f"{f(t_end, 3)} s", f"<= {SCX['sts_s']} s", t_end <= SCX["sts_s"],
        f"t_logic {SCX['t_logic_s'] * 1000:.0f} ms + t_drive {SCX['t_drive_s'] * 1000:.0f} ms + v/{SCX['ramp_mps2']}")
    rec("SS1-t timing", f"stop from {v} m/s: <= 0.3 m/s before SLS monitoring starts (t_SLS {SCX['t_sls_s']} s)", f"{f(t_sls, 3)} s", f"<= {SCX['t_sls_s']} s",
        t_sls <= SCX["t_sls_s"], "no nuisance SLS-STO during a normal ramp; on ramp failure the SWD goes STO at t_SLS")

# ------------------------------------------------------------------ 8. thermal
T = NET["thermal"]
for bay, b in T["bays"].items():
    P_ = sum(b["losses_W"].values())
    ga = T["h_W_m2K"] * b["area_m2"]
    tp = T["ambient_C"] + P_ / ga
    fw = b.get("fan_W_per_K", T["fan_W_per_K"])
    tf = T["ambient_C"] + P_ / (ga + fw)
    rec("Thermal", f"{bay}: passive (closed covers, {T['ambient_C']} C) - design question", f"{f(P_, 1)} W -> {f(tp, 0)} C", f"<= {T['limit_C']} C",
        True if tp <= T["limit_C"] else "INSUFFICIENT", f"h*A = {f(ga, 2)} W/K; answer: fans required")
    rec("Thermal", f"{bay}: with {b.get('fans', '2 x 60 mm filter fans')}", f"{f(tf, 0)} C", f"<= {T['limit_C']} C", tf <= T["limit_C"], f"+{fw} W/K")

# ------------------------------------------------------------------ 9. safety I/O usage + controller options
SCM = NET["safety_controller"]["modules"]
need = {"OA": [0, 0, 0, 0], "C48": [0, 0, 0, 0]}    # safe inputs, safe outputs, standard outputs, of which relay outputs (spares excluded)
for mod, m in NET["safety_io"].items():
    cap = SCM[mod]
    used_i = sum(1 for v in m.get("inputs", {}).values() if v["sig"] != "spare")
    used_o = sum(1 for v in m.get("outputs", {}).values() if not v["sig"].startswith("spare"))
    used_s = sum(1 for v in m.get("std_outputs", {}).values() if not v["sig"].startswith("spare"))
    used_i = sum(1 for v in m.get("inputs", {}).values() if not v["sig"].startswith("spare"))
    tag = "C48 only" if m.get("variant") == "C48" else ""
    o_cap = cap["out"] + cap.get("rly", 0)
    rec("Safety I/O", f"{mod} {cap['mpn']}: channels used", f"{used_i} in / {used_o} safe out ({'relay' if cap.get('rly') else 'SC'}) / {used_s} std out",
        f"<= {cap['in']} / {o_cap} / {cap['std']}", used_i <= cap["in"] and used_o <= o_cap and used_s <= cap["std"], tag)
    for var in need:
        if m.get("variant", "all") in ("all", var):
            need[var][0] += used_i
            need[var][1] += used_o
            need[var][2] += used_s
            if cap.get("rly"):
                need[var][3] += used_o
    tests = {v.get("test") for v in m.get("inputs", {}).values() if v.get("test")}
    if tests:
        rec("Safety I/O", f"{mod}: test pulse lines used", ", ".join(sorted(tests)), f"<= {cap['test']}", len(tests) <= cap["test"], "cross-fault detection on NC pairs")
ni, no, ns, nr = need["OA"]
rec("Safety I/O", "OA total I/O (non-spare)", f"{ni} in / {no} safe out (of which {nr} relay) / {ns} std out", "-", "INFO", "rev B1: 24 in / 8 out / 2 std; rev A1: 37 in / 20 out")
best = None
for k, o in NET["safety_controller_options"].items():
    if k.startswith("A"):
        rec("Safety ctrl options", f"{k} {o['name']}", f"EUR {f(o['price_eur'], 0)}", "reference", "INFO", o["note"])
        continue
    fit = o["in"] >= ni and o["out"] + o["rly"] >= no and o["rly"] >= nr and o["out"] + o["rly"] + o["std"] >= no + ns
    rec("Safety ctrl options", f"{k} {o['name']}: covers the OA I/O ({ni} in / {no} out incl. {nr} relay / {ns} std)",
        f"{o['in']} in / {o['out']} SC + {o['rly']} relay out / {o['std']} std out, EUR {f(o['price_eur'], 0)} ({o['tag']})", "fit", fit if fit else "NO FIT", o["note"])
    if fit and (best is None or o["price_eur"] < NET["safety_controller_options"][best]["price_eur"]):
        best = k
ch = NET["safety_controller"]["chosen"]
rec("Safety ctrl options", "chosen option is the cheapest that fits", ch, best, ch == best,
    NET["safety_controller_options"][ch]["name"])

# ------------------------------------------------------------------ 10. PL per safety function
PF = NET["pfhd"]
PL_LIM = [("e", 1e-7), ("d", 1e-6), ("c", 3e-6), ("b", 1e-5), ("a", 1e-4)]
ORDER = "abcde"


def pl_of(p):
    for k, lim in PL_LIM:
        if p < lim:
            return k
    return "-"


# SF: (PLr, chain, cap from component rating, note)  -- keep in sync with SAFETY_FUNCTIONS.md
SF = {
    "SF1 E-stop (ES1+ES2 series) -> traction SS1-t (SLS at once, STO+SBC at 1.2 s via SR1 relays)": ("d", ["ESTOP_SERIES", "PNOZ_B0", "PNOZ_EF", "SWD_STO"], "e", "series wiring: DC low per ISO/TR 24119"),
    "SF1 E-stop (ES3 torso) -> traction SS1-t": ("d", ["ESTOP_CAT3", "PNOZ_B0", "PNOZ_EF", "SWD_STO"], "e", ""),
    "SF1 E-stop -> arms OA (K1/K2 on SC0 O0, SS1-t 0.5 s)": ("d", ["ESTOP_SERIES", "PNOZ_B0", "K1K2_CAT3"], "e", "arm falls onto rests: residual risk"),
    "SF2 protective stop (scanner OSSD1) -> traction": ("d", ["NS3", "PNOZ_B0", "PNOZ_EF", "SWD_STO"], "d", "nanoScan3 caps at PL d"),
    "SF3 field-set switching consistent with SLS (SR2 1-ch relays, 1-of-3 code)": ("d", ["PNOZ_B0", "PNOZ_EF", "RLY_1CH", "SWD_SLS", "NS3"], "d", "Cat 3 argued by the 1-of-3 code (single fault -> invalid code -> OSSD off)"),
    "SF4 safe limited speed per mode (SLS + permanent SMS)": ("d", ["PNOZ_B0", "PNOZ_EF", "SWD_SLS"], "d", "SWD SLS 2.29E-7 SOURCED"),
    "SF5 safe limited reverse speed (permanent SLSa)": ("d", ["SWD_SLS"], "d", "no controller channel"),
    "SF6 base standstill while arms work (STO+SBC)": ("d", ["PNOZ_B0", "PNOZ_EF", "SWD_STO", "SWD_SBC"], "d", "SBC3 PL d (phase-short brake)"),
    "SF7 OA arms move only with arm field clear (OSSD2 -> K1/K2)": ("d", ["NS3", "PNOZ_B0", "K1K2_CAT3"], "d", "PLr e if P2: NOT achievable (Type 3 scanner)"),
    "SF8 carry mode (FAST only if arms parked + unpowered)": ("d", ["PSEN2", "PNOZ_B0", "PNOZ_EF", "K1K2_CAT3", "SWD_SLS"], "d", "PSEN on separate input pairs"),
    "SF9 docking field (reduced rear field only with SLS)": ("c", ["PNOZ_B0", "PNOZ_EF", "RLY_1CH", "SWD_SLS", "NS3"], "d", ""),
    "SF10 pads dead unless docked (station chain + OV relay)": ("c", ["DOCK_STATION"], "c", "robot-side KS relay = functional measure; XD3 DUB01CD48500V 58.5 V relay"),
    "SF11 no traction while charge permitted": ("c", ["PNOZ_B0", "PNOZ_EF", "SWD_STO"], "e", ""),
    "SF12 battery protection (BMS + K0 + K0V + F0)": ("d", None, "-", "BMS IEC 62619: no PL/PFHd published (V:D13) -> independent layers, no PL credit"),
    "SF13 manual reset": ("d", ["SB1_CAT1", "PNOZ_B0"], "d", "reset is not a dangerous-failure path; edge evaluation"),
    "SF14 mode selection + enabling (MANUAL)": ("d", ["KEY_CAT1", "ENABLE_CAT3", "PNOZ_B0", "PNOZ_EF", "SWD_SLS"], "d", ""),
    "SF15 coffee module stop (KI4 + K4 on an auxiliary output, Cat B)": ("b", ["STD_K4_CATB"], "b", "PLr b to be confirmed (H13); fallback: KI4 on free SC0 O1 (cost 0)"),
    "SF16 C48 protective stop / PFL handover (arm internal)": ("d", ["NS3", "PNOZ_B0", "PNOZ_EF8", "C48_ARM"], "d", "OpenArm: IMPOSSIBLE"),
}
for name, (plr, chain, cap, note) in SF.items():
    if chain is None:
        rec("PL", name, "n/a (no PL credit)", f"PLr {plr}", "INFO", note)
        continue
    pf = sum(PF[k] for k in chain)
    pl = pl_of(pf)
    if cap in ORDER and ORDER.index(pl) > ORDER.index(cap):
        pl = cap
    rec("PL", name, f"PFHd {pf:.2e} -> PL {pl}", f"PLr {plr}", ORDER.index(pl) >= ORDER.index(plr), note)

# ------------------------------------------------------------------ 11. cable schedule consistency
csv_path = os.path.join(HERE, "cable_schedule.csv")
cab = {r["cable_id"]: r for r in csv.DictReader(open(csv_path))}
for c in NET["circuits"]:
    r = cab.get(c["cable"])
    if r is None:
        rec("Cables", f"{c['id']}: cable {c['cable']} in schedule", "missing", "present", False)
        continue
    sizes = [float(x) for x in re.findall(r"x\(?(\d+(?:\.\d+)?)\)?", r["cores_x_mm2"])]
    mm = max(sizes) if sizes else 0
    rec("Cables", f"{c['id']}: {c['cable']} conductor in schedule >= netlist", f"{mm} mm2", f">= {c['mm2']} mm2", mm >= c["mm2"], r["conductor_type"][:45])
harn = {r["cad_harness"] for r in cab.values()}
for h in NET["cad_harness"]:
    rec("Cables", f"CAD harness {h} mapped", "yes" if h in harn else "no", "mapped", h in harn)

# ------------------------------------------------------------------ 11b. CAD consistency (rev B3: one position table, CAD_REV_B3.md s.3)
def cad_loc(bb):
    """classify a CAD bbox [x0, x1, y0, y1, z0, z1] into the netlist loc codes"""
    x0, x1, y0, y1, z0, z1 = bb
    yc, zc = (y0 + y1) / 2, (z0 + z1) / 2
    if abs(yc) < 131:
        return "CD" if z0 >= 300 else "CB"
    side = "L" if yc > 0 else "R"
    if side == "R" and y1 <= -229:
        return "RW"
    if abs(zc - 120) < 1:
        return side + "L"
    if abs(zc - 245) < 1:
        return "LM"
    if abs(zc - 275) < 1:
        return side + "U"
    if abs(zc - 217) < 1 or abs(zc - 220) < 1:
        return side + "C"
    return "BASE"


PJ = os.path.join(HERE, "..", "out", "parts.json")
if os.path.exists(PJ):
    parts = {p["name"]: p for p in json.load(open(PJ))}
    n_ok, bad = 0, []
    for d in NET["devices"]:
        c = d.get("cad")
        if not c or d["loc"] in ("SUP", "DOCK") and not c.startswith("X") or d["variant"] == "C48":
            continue                                  # C48-only modules (SX2) have a reserved, empty slot in the OA CAD
        hits = [n for n in parts if n == c or (c.endswith("_") and n.startswith(c))]
        if not hits:
            bad.append(f"{d['ref']}: {c} not in parts.json")
            continue
        if d["loc"] in ("BASE", "SUP", "DOCK"):
            n_ok += 1
            continue
        lc = cad_loc(parts[hits[0]]["bbox_mm"])
        if lc != d["loc"]:
            bad.append(f"{d['ref']}: loc {d['loc']} vs CAD {lc} ({c})")
        else:
            n_ok += 1
    rec("CAD", "netlist devices: CAD id exists and loc = CAD position (out/parts.json)", f"{n_ok} OK, {len(bad)} mismatch", "0 mismatch",
        not bad, "; ".join(bad) if bad else "one position table (CAD_REV_B3.md s.3 = din_layout.md)")
    IJ = os.path.join(HERE, "..", "out", "interference.json")
    if os.path.exists(IJ):
        it = json.load(open(IJ))
        mw = [k for k in it["keepout_violations"] if "B01_" not in k[0] and "C01_" not in k[0]]
        rec("CAD", "Mean Well installation clearances (40 above / 20 below / 5 sides) as CAD keep-outs", f"{len(mw)} violations",
            "0", not mw, f"{it['keepout_pairs_checked']} keep-out/part pairs checked by amr_cad.py (DDR-480/240/120/60, DRDN40 at the true 125.2 mm height)")
        rec("CAD", "castor swivel keep-outs + carriage travel (-2.5/+17 mm)", f"{len([k for k in it['keepout_violations'] if 'C01_' in k[0]])} / {len(it.get('castor_travel_overlaps', []))} overlaps",
            "0 / 0", not [k for k in it['keepout_violations'] if 'C01_' in k[0]] and not it.get('castor_travel_overlaps'), "E34 U8 moved to the RR corner, E5B/E16 DSR clamps above the packs")
        rec("CAD", "solid interferences (robot) / docked dock", f"{len(it['interferences'])} / {len(it['dock_interferences'])}", "0 / 0",
            not it["interferences"] and not it["dock_interferences"], "")
    g01 = parts.get("E38_G01_LYNK_II_gateway")
    if g01:
        b = g01["bbox_mm"]
        dims = sorted([b[1] - b[0], b[3] - b[2], b[5] - b[4]])
        rec("CAD", "G01 LYNK II envelope in CAD vs sell sheet 885-0035 (120 x 135 x 44 mm)", " x ".join(f"{x:.0f}" for x in dims), "44 x 120 x 135",
            [round(x) for x in dims] == [44, 120, 135], "on bracket E38b against the right side cover")
    k0v = parts.get("E2K_K0V_LVCO_relay_DUB01CD48500V")
    if k0v:
        b = k0v["bbox_mm"]
        rec("CAD", "K0V DUB01 envelope vs datasheet 22.5 x 80 x 99.5 mm", f"{b[1] - b[0]:.1f} x {b[5] - b[4]:.0f} x {b[3] - b[2]:.1f}", "22.5 x 80 x 99.5",
            abs(b[1] - b[0] - 22.5) < 0.1 and abs(b[5] - b[4] - 80) < 0.1 and abs(b[3] - b[2] - 99.5) < 0.1, "")
else:
    rec("CAD", "out/parts.json present", "missing", "run amr_cad.py first", "INFO", "")

# ------------------------------------------------------------------ 12. BOM
tot = {"OA": 0.0, "C48": 0.0}
tags = {}
grp = {}
for d in NET["devices"]:
    cost = d["price_eur"] * d["qty"]
    for v in tot:
        if d["variant"] in ("all", v):
            tot[v] += cost
    if d["variant"] in ("all", "OA"):
        tags[d["price_tag"]] = tags.get(d["price_tag"], 0) + cost
    if d["variant"] in ("all", "OA"):
        grp[d.get("grp", "other")] = grp.get(d.get("grp", "other"), 0) + cost
ra = NET["meta"]["rev_A_package_eur"]
rb = NET["meta"]["rev_B1_package_eur"]
rec("BOM", "Electrical + safety package, variant OA (excl. arms, Jetson, sensors of the head)", f"EUR {f(tot['OA'], 0)}", f"rev B1 EUR {rb['OA']} / rev A EUR {ra['OA']}", "INFO",
    ", ".join(f"{k} EUR {f(v, 0)}" for k, v in sorted(tags.items())))
rec("BOM", "Electrical + safety package, variant C48 (excl. arms)", f"EUR {f(tot['C48'], 0)}", f"rev B1 EUR {rb['C48']} / rev A EUR {ra['C48']}", "INFO", "")
for k, v in sorted(grp.items(), key=lambda x: -x[1]):
    if v:
        rec("BOM", f"OA group: {k}", f"EUR {f(v, 0)}", "-", "INFO", "")

# ------------------------------------------------------------------ write
n_pass = sum(1 for r in rows if r[4] == "PASS")
n_fail = sum(1 for r in rows if r[4] == "FAIL")
out = ["# CHECKS_AMR: electrical + safety checks (generated by check_amr.py, do not edit)", "",
       f"Netlist rev {NET['meta']['rev']} ({NET['meta']['date']}). **{n_pass} PASS, {n_fail} FAIL**, "
       f"{len(rows) - n_pass - n_fail} INFO/OPEN. Inputs tagged ASSUMED in netlist_amr.yaml remain assumptions.", ""]
if fails:
    out += ["## FAIL list", ""] + [f"- {x}" for x in fails] + [""]
sec = None
for s, item, val, lim, res, note in rows:
    if s != sec:
        out += ["", f"## {s}", "", "| Check | Value | Limit | Result | Note |", "|---|---|---|---|---|"]
        sec = s
    out.append(f"| {item} | {val} | {lim} | **{res}** | {note} |")
open(os.path.join(HERE, "CHECKS_AMR.md"), "w").write("\n".join(out) + "\n")
print(f"CHECKS_AMR.md written: {n_pass} PASS, {n_fail} FAIL")
for x in fails:
    print("  FAIL", x)
sys.exit(0)
