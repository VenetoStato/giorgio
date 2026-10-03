#!/usr/bin/env python3
"""Giorgio electrical design validation.

Loads netlist.yaml and checks:
  * battery: SELV/PELV limit, EU 2023/1542 2 kWh threshold, charger CV per cell
  * prospective short-circuit current of the LFP pack (from internal resistance)
  * DC-DC sizing vs continuous loads (80 % derating) and simultaneous peaks
  * pack current / C-rate / BMS limits with ALL peaks at once, pack sag vs DC-DC UVLO
  * per-branch wire ampacity (base table x ambient x grouping), voltage drop
    (<3 % power, <5 % elsewhere), fuse selection (In >= 1.25 I_cont, In <= Iz,
    V_dc rating, DC breaking capacity >= Isc at that point, no blow on peaks)
  * contactors: DC break of worst-case current, mirror contacts
  * precharge: tau, time to 95 %, resistor energy and average power
  * regen clamp window on the 24 V arm buses, clamp resistor sizing
  * autonomy for three duty profiles (pack, Tracer, combined with energy balancing)
  * charge time (dock CC/CV, Tracer charged by the onboard isolated charger)
  * coffee options A/B/C: peak current, C-rate, energy per cup, main fuse/cable impact
  * safety functions: PFHd sum vs PL d (unknown/unrated elements -> FAIL)
  * BOM total

Usage:  python3 calc.py [netlist.yaml] [CHECKS.md]      (Python 3 + PyYAML only)
Exit code 1 if any FAIL.
"""
import math
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RHO_CU_20 = 0.017241          # ohm mm^2 / m
ALPHA_CU = 0.00393            # 1/K
T_COND = 70.0                 # conductor temperature for voltage drop (PVC max)

results = []                  # (section, item, value, limit, status, note)


def rec(section, item, value, limit, ok, note=""):
    status = "INFO" if ok is None else ("PASS" if ok else "FAIL")
    results.append((section, item, value, limit, status, note))
    return ok


def interp(table, x):
    pts = sorted((float(k), float(v)) for k, v in table.items())
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


class Net:
    def __init__(self, path):
        self.d = yaml.safe_load(Path(path).read_text())
        d = self.d
        self.b = d["battery"]
        self.bus = {x["id"]: x for x in d["buses"]}
        self.comp = {c["id"]: c for c in d["components"]}
        self.load = {x["id"]: x for x in d["loads"]}
        self.conv = {x["id"]: x for x in d["converters"]}
        self.fuse = {x["id"]: x for x in d["fuses"]}
        self.br = {x["id"]: x for x in d["branches"]}
        cell = self.b["cell"]
        self.ns, self.np = self.b["series"], self.b["parallel"]
        self.v_nom = self.ns * cell["v_nom"]
        self.v_max = self.ns * cell["v_max"]
        self.v_min = self.ns * cell["v_min_cutoff"]
        self.ah = self.np * cell["ah"]
        self.e_nom = self.v_nom * self.ah
        self.main = d.get("main_bus", "B48")
        mb = self.bus[self.main]
        self.v_min_bus = min(self.v_min, mb.get("v_min", self.v_min)) if d.get("main_bus") else self.v_min

    # ---- resistances
    def r_pack(self, worst):
        c = self.b["cell"]
        r_cell = c["r_ac_mohm"] if worst == "min" else c["r_dc_mohm"]
        r = self.ns * r_cell / self.np + self.b["r_interconnect_mohm"]
        r += self.b["r_bms_path_min_mohm"] if worst == "min" else self.b["r_bms_path_mohm"]
        return r / 1000.0

    # ---- load / converter currents
    def bus_power(self, bus_id, kind):
        return sum(l[f"p_{kind}_w"] for l in self.load.values() if l["bus"] == bus_id)

    def conv_out_current(self, cid, kind):
        c = self.conv[cid]
        i = self.bus_power(c["out_bus"], kind) / self.bus[c["out_bus"]]["v_nom"]
        if kind == "peak":
            i = min(i, c["iout_a"] * c.get("peak_factor", 1.0))
        return i

    def conv_in_power(self, cid, kind):
        c = self.conv[cid]
        return self.conv_out_current(cid, kind) * self.bus[c["out_bus"]]["v_nom"] / c["eta"]

    def excl_saving(self, kind):
        """pack-side W that can never flow together (energy-management interlocks): sum of the smaller members"""
        sav = 0.0
        for g in self.d.get("exclusive", []):
            if "sets" in g:     # groups of loads that never run together: keep only the largest set
                vals = [sum(self.load[l][f"p_{kind}_w"] for l in st) for st in g["sets"]]
            else:
                vals = [self.load[l][f"p_{kind}_w"] for l in g.get("loads", [])]
                vals += [self.conv_in_power(c, kind) for c in g.get("convs", [])]
            sav += sum(vals) - max(vals)
        return sav

    def branch_current(self, bid):
        br = self.br[bid]
        cur = br["current"]
        f = cur["from"]
        if f == "conv_in":
            ic = sum(self.conv_in_power(c, "cont") for c in cur["convs"]) / self.v_min
            ip = sum(self.conv_in_power(c, "peak") for c in cur["convs"]) / self.v_min
            ps = max(self.conv[c].get("peak_s", 1) for c in cur["convs"])
        elif f == "conv_out":
            ic = self.conv_out_current(cur["conv"], "cont")
            ip = self.conv_out_current(cur["conv"], "peak")
            ps = self.conv[cur["conv"]].get("peak_s", 1) or 1
        elif f == "loads":
            vs = [self.v_min if self.load[x]["bus"] == self.main else self.bus[self.load[x]["bus"]]["v_nom"] for x in cur["loads"]]
            ic = sum(self.load[x]["p_cont_w"] / v for x, v in zip(cur["loads"], vs))
            ip = sum(self.load[x]["p_peak_w"] / v for x, v in zip(cur["loads"], vs))
            ps = max(self.load[x].get("peak_s", 1) for x in cur["loads"])
        elif f == "load":
            l = self.load[cur["load"]]
            v = self.v_min if l["bus"] == self.main else self.bus[l["bus"]]["v_nom"]
            ic, ip, ps = l["p_cont_w"] / v, l["p_peak_w"] / v, l.get("peak_s", 1)
        elif f == "sum":
            parts = [self.branch_current(x) for x in cur["branches"]]
            ic = sum(p[0] for p in parts) - self.excl_saving("cont") / self.v_min
            ip = sum(p[1] for p in parts) - self.excl_saving("peak") / self.v_min
            ps = max([p[2] for p in parts if p[1] > p[0] + 1e-9] or [1])
        elif f == "fixed":
            ic, ip, ps = cur["i_cont_a"], cur["i_peak_a"], cur.get("peak_s", 1)
        else:
            raise ValueError(f)
        return ic, ip, ps


def main(path_yaml, path_md):
    n = Net(path_yaml)
    d, b = n.d, n.b
    comp = n.comp

    # ================================================================ battery & regulatory
    rec("Battery & regulatory", f"{n.ns}s{n.np}p LFP nominal energy", f"{n.e_nom:.0f} Wh ({n.v_nom:.1f} V x {n.ah:.0f} Ah)",
        "<= 2000 Wh (EU 2023/1542: passport / carbon footprint duties above 2 kWh)", n.e_nom <= 2000)
    rec("Battery & regulatory", "Max pack voltage (3.65 V/cell)", f"{n.v_max:.2f} V",
        "<= 60 V ripple-free DC (IEC 60204-1 6.4 PELV, dry location)", n.v_max <= 60)
    if "charging" in d:
        cv = d["charging"]["cv_v"]
        rec("Battery & regulatory", "Dock charger CV setpoint", f"{cv:.2f} V = {cv / n.ns:.3f} V/cell", "<= 3.65 V/cell", cv / n.ns <= 3.65)
    for c in n.conv.values():
        rec("Battery & regulatory", f"{c['id']} input range ({comp[c['component']]['mpn']})", f"{c['vin_min']}-{c['vin_max']} V",
            f"covers {n.v_min:.1f}-{n.v_max:.2f} V", c["vin_min"] <= n.v_min and c["vin_max"] >= n.v_max)
    msd = comp["MSD"]["ratings"]
    rec("Battery & regulatory", "Service disconnect (MSD) rating", f"{msd['i_cont_a']} A / {msd['v_dc']} V",
        f">= main fuse and >= {n.v_max:.1f} V", msd["v_dc"] >= n.v_max and msd["i_cont_a"] >= comp[n.fuse["F0"]["component"]]["ratings"]["in_a"],
        "not a load-break device: opened only after key-off (BMS FETs open)")

    # ================================================================ short circuit
    r_min, r_max = n.r_pack("min"), n.r_pack("max")
    isc = n.v_max / r_min
    rec("Short circuit", "Pack resistance, min (AC-IR, cold) / max (DC-IR, aged)", f"{r_min * 1e3:.2f} / {r_max * 1e3:.2f} mOhm", "", None,
        f"{n.ns} x {b['cell']['r_ac_mohm']} mOhm + interconnect {b['r_interconnect_mohm']} + BMS path {b['r_bms_path_min_mohm']} mOhm")
    rec("Short circuit", "Prospective bolted short-circuit current at pack terminals", f"{isc / 1000:.2f} kA", "", None,
        "V_max / R_min; BMS short-circuit trip NOT credited (it is a second layer)")

    # ================================================================ DC-DC sizing
    for c in n.conv.values():
        ob = n.bus[c["out_bus"]]
        ic = n.bus_power(c["out_bus"], "cont") / ob["v_nom"]
        ip = n.bus_power(c["out_bus"], "peak") / ob["v_nom"]
        k_mount = 1.0
        if c.get("mount") == "lying":
            k_nofan = c.get("derate_lying", 1.0)
            rec("DC-DC sizing", f"{c['id']} lying mount WITHOUT forced air (derate {k_nofan})",
                f"{ic:.2f} A cont / {ip:.2f} A peak", f"<= {0.8 * c['iout_a'] * k_nofan:.1f} A / {c['iout_a'] * c.get('peak_factor', 1.0) * k_nofan:.1f} A", None,
                ("would FAIL" if ic > 0.8 * c["iout_a"] * k_nofan or ip > c["iout_a"] * c.get("peak_factor", 1.0) * k_nofan else "would pass")
                + "; Mean Well curve is for vertical mounting (100 % to 55 C, 40 % at 80 C); lying derate is an assumption")
            k_mount = 1.0 if c.get("fan") else k_nofan
        cap_p = c["iout_a"] * c.get("peak_factor", 1.0) * k_mount
        mpn = comp[c["component"]]["mpn"] + (" lying + fan" if c.get("mount") == "lying" and c.get("fan") else "")
        rec("DC-DC sizing", f"{c['id']} {mpn} -> {ob['id']} continuous", f"{ic:.2f} A ({ic * ob['v_nom']:.0f} W)",
            f"<= 80 % of {c['iout_a'] * k_mount:.1f} A = {0.8 * c['iout_a'] * k_mount:.1f} A", ic <= 0.8 * c["iout_a"] * k_mount + 1e-9)
        rec("DC-DC sizing", f"{c['id']} simultaneous peak of all its loads", f"{ip:.2f} A ({ip * ob['v_nom']:.0f} W)",
            f"<= {cap_p:.1f} A ({c.get('peak_s', 0)} s)", ip <= cap_p + 1e-9, c.get("peak_note", ""))

    # ================================================================ pack current
    loads_b48 = [l for l in n.load.values() if l["bus"] == n.main]
    p_peak = sum(n.conv_in_power(c, "peak") for c in n.conv) + sum(l["p_peak_w"] for l in loads_b48) - n.excl_saving("peak")
    p_cont = sum(n.conv_in_power(c, "cont") for c in n.conv) + sum(l["p_cont_w"] for l in loads_b48) - n.excl_saving("cont")
    i_peak, i_cont = p_peak / n.v_min, p_cont / n.v_min
    bf = d.get("buffer")
    if bf:   # peak buffer behind a current-limited port share for the arm bus
        arm_pk = sum(n.load[x]["p_peak_w"] for x in bf["feeds"]) / n.v_min
        arm_ct = sum(n.load[x]["p_cont_w"] for x in bf["feeds"]) / n.v_min
        share = bf["port_share_a"]
        i_buf = max(0.0, arm_pk - share)
        rec("Peak buffer", f"Arm peak current above the port share ({share} A current-limited ORing)", f"{i_buf:.1f} A from the buffer for {bf['peak_s']} s",
            f"<= buffer pulse {bf['i_pulse_a']} A", i_buf <= bf["i_pulse_a"], comp[bf["component"]]["mpn"])
        rec("Peak buffer", "Arms sustained current covered by the port share alone", f"{arm_ct:.1f} A", f"<= {share} A", arm_ct <= share)
        e_evt = (arm_pk - share) * n.v_min * bf["peak_s"] / 3600
        rec("Peak buffer", "Energy per peak event / recharge time at the charger current", f"{e_evt:.2f} Wh / {e_evt / (bf['chg_a'] * 27) * 60:.1f} min",
            f"<= 10 % of {bf['e_wh']} Wh", e_evt <= 0.1 * bf["e_wh"], f"charger {bf['chg_a']} A gets the leftover port power (power manager)")
        i_peak = i_peak - arm_pk + min(arm_pk, share)        # what the base port sees
        i_cont = i_cont - arm_ct + min(arm_ct, share)
        p_peak, p_cont = i_peak * n.v_min, i_cont * n.v_min
    bms = comp[b["bms_component"]]["ratings"]
    cell = b["cell"]
    rec("Pack current", "ALL loads at declared peak at once (interlocks applied) at V_min",
        f"{p_peak:.0f} W -> {i_peak:.1f} A = {i_peak / n.ah:.2f} C",
        f"<= min({comp[b['bms_component']]['short'] or 'BMS'} {bms['i_peak_a']} A/{bms['t_peak_s']} s, cell {cell['c_pulse']} C = {cell['c_pulse'] * n.ah:.0f} A)",
        i_peak <= min(bms["i_peak_a"], cell["c_pulse"] * n.ah), "physically unlikely combination; design worst case")
    rec("Pack current", "All loads at max sustained at V_min", f"{p_cont:.0f} W -> {i_cont:.1f} A = {i_cont / n.ah:.2f} C",
        f"<= min({comp[b['bms_component']]['short'] or 'BMS'} {bms['i_cont_a']} A, cell {cell['c_cont']} C = {cell['c_cont'] * n.ah:.0f} A)",
        i_cont <= min(bms["i_cont_a"], cell["c_cont"] * n.ah))
    sag = i_peak * r_max
    uvlo = max(c["vin_min"] for c in n.conv.values())
    v_low = n.v_ns_low = n.ns * 3.0      # 10 % SoC resting voltage ~3.0 V/cell
    rec("Pack current", "Pack voltage under all-peak load at 10 % SoC (3.0 V/cell, DC-IR max)",
        f"{v_low - sag:.1f} V (sag {sag:.2f} V)", f"> DC-DC UVLO {uvlo} V + 2 V margin", v_low - sag > uvlo + 2)
    rt = d.get("ride_through_v", uvlo)
    rec("Pack current", f"Pack voltage under all-peak load at cut-off ({b['cell']['v_min_cutoff']} V/cell)",
        f"{n.v_min - sag:.1f} V", f"> {rt} V (DC-DC UVLO / ride-through)", n.v_min - sag > rt,
        "BMS/Jetson must start a controlled shutdown at 10 % SoC; below that peaks may brown out the arm DC-DCs")

    # ================================================================ branches
    for bid, br in n.br.items():
        bus = n.bus[br["bus"]]
        ic, ip, ps = n.branch_current(bid)
        br["_ic"], br["_ip"] = ic, ip
        tab = d["wiring"]["ampacity_table"][br["method"]]
        base = tab[float(br["csa_mm2"])] if float(br["csa_mm2"]) in tab else tab[br["csa_mm2"]]
        kt = interp(d["wiring"]["ambient_correction"], br["ambient_c"])
        kg = interp(d["wiring"]["grouping_correction"], br["grouped"])
        iz = base * kt * kg
        tag = f"{bid} {br['desc']}"
        rec("Wiring ampacity", tag, f"{ic:.1f} A cont / {ip:.1f} A peak, {br['csa_mm2']} mm2",
            f"Iz {iz:.1f} A = {base} x {kt:.2f} (T {br['ambient_c']} C) x {kg:.2f} (n={br['grouped']})", ic <= iz)
        if ip > iz:
            rec("Wiring ampacity", tag + " - short peak", f"{ip:.1f} A for {ps} s", f"<= 1.5 Iz = {1.5 * iz:.1f} A for <= 10 s",
                ip <= 1.5 * iz and ps <= 10, "conductor thermal time constant >> peak (assumption)")
        rho = RHO_CU_20 * (1 + ALPHA_CU * (T_COND - 20))
        r_loop = rho * 2 * br["length_m"] / br["csa_mm2"]
        v_ref = bus["v_min"] if bus["id"] == n.main else bus["v_nom"]
        vd, vdp = ic * r_loop, ip * r_loop
        lim = br["vdrop_limit_pct"]
        rec("Voltage drop", tag, f"{100 * vd / v_ref:.2f} % ({vd * 1000:.0f} mV @ {ic:.1f} A)", f"< {lim} % (ref {v_ref} V)",
            100 * vd / v_ref < lim, f"loop {2 * br['length_m']:.1f} m, {r_loop * 1e3:.1f} mOhm @ {T_COND:.0f} C; at peak {100 * vdp / v_ref:.2f} %")
        br["_r_loop"] = r_loop
        if not br.get("fuse"):
            continue
        fz = comp[n.fuse[br["fuse"]]["component"]]
        fr = fz["ratings"]
        In = fr["in_a"]
        fl = f"{br['fuse']} {fz['mpn']} ({bid})"
        rec("Fuse selection", fl + ": In >= 1.25 I_cont", f"{In} A", f">= {1.25 * ic:.1f} A", In >= 1.25 * ic - 1e-9)
        rec("Fuse selection", fl + ": In <= Iz (cable protected)", f"{In} A", f"<= {iz:.1f} A", In <= iz + 1e-9)
        rec("Fuse selection", fl + ": DC voltage rating", f"{fr['v_dc']} V", f">= {bus['v_max']} V", fr["v_dc"] >= bus["v_max"])
        if bus["id"] == n.main and not br.get("isc_override_a"):
            r_up = r_min + sum(br.get("upstream_r_mohm", [])) / 1000.0
            isc_here = n.v_max / r_up
            note = f"R_pack,min + upstream {sum(br.get('upstream_r_mohm', [])):.2f} mOhm"
        else:
            isc_here = br.get("isc_override_a", 0)
            note = br.get("note", "source current-limited (DC-DC) or declared")
        rec("Fuse selection", fl + ": DC breaking capacity", f"{fr['ir_dc_a'] / 1000:.1f} kA", f">= Isc {isc_here / 1000:.2f} kA",
            fr["ir_dc_a"] >= isc_here, note + (" | IR value assumed - verify" if fz.get("assumed") else ""))
        rec("Fuse selection", fl + ": no blow on peak", f"{ip / In:.2f} x In for {ps} s",
            f"<= {fr['no_blow_ratio']} x In", ip / In <= fr["no_blow_ratio"] + 1e-9, fr.get("no_blow_note", ""))

    # ================================================================ contactors
    for k in d["contactors"]:
        c = comp[k["component"]]
        r = c["ratings"]
        rec("Contactors", f"{k['id']} {c['mpn']} carry", f"{k['i_cont_a']:.1f} A", f"<= {r['i_cont_a']} A", k["i_cont_a"] <= r["i_cont_a"])
        rec("Contactors", f"{k['id']} worst-case DC break", f"{k['i_break_a']:.1f} A @ {k['v_dc']} V",
            f"<= {r['i_break_a']} A @ {r['v_break_v']} V", k["i_break_a"] <= r["i_break_a"] and k["v_dc"] <= r["v_break_v"],
            r.get("break_note", "") + ("; " + k["note"] if k.get("note") else ""))
        rec("Contactors", f"{k['id']} feedback contact for PNOZ EDM", r.get("aux", "none"), "mirror contact (IEC 60947-4-1 Annex F)",
            bool(r.get("mirror_contact")))
    arm_peak_in = n.branch_current("W02")[1]
    rec("Contactors", "Declared worst-case break current covers derived arm-feed peak", f"{arm_peak_in:.1f} A (derived)",
        f"<= declared {d['contactors'][0]['i_break_a']} A", arm_peak_in <= d["contactors"][0]["i_break_a"])

    # ================================================================ precharge
    for pc in d["precharge"]:
        rz = comp[pc["resistor"]]["ratings"]
        C = pc["c_total_uf"] * 1e-6
        R = rz["r_ohm"]
        tau = R * C
        t95 = -tau * math.log(1 - pc["done_fraction"])
        e = 0.5 * C * n.v_max ** 2
        rec("Precharge", f"{pc['id']} tau = R C", f"{tau * 1000:.0f} ms", "", None, f"R {R} ohm, C {pc['c_total_uf']} uF ({pc['c_note']})")
        rec("Precharge", f"{pc['id']} time to {pc['done_fraction'] * 100:.0f} % before K2 closes", f"{t95:.2f} s", f"<= {pc['t_max_s']} s", t95 <= pc["t_max_s"])
        rec("Precharge", f"{pc['id']} resistor energy per precharge (= 1/2 C V^2)", f"{e:.1f} J", f"<= {rz['e_pulse_j']} J pulse",
            e <= rz["e_pulse_j"], rz.get("pulse_note", ""))
        rec("Precharge", f"{pc['id']} initial resistor current / power", f"{n.v_max / R:.2f} A / {n.v_max ** 2 / R:.0f} W", "decays with tau", None)
        pav = e * pc["repeat_per_min"] / 60
        rec("Precharge", f"{pc['id']} average power at {pc['repeat_per_min']} cycles/min (reset retries)", f"{pav:.2f} W", f"<= {rz['p_cont_w']} W", pav <= rz["p_cont_w"])
        rec("Precharge", f"{pc['id']} residual step at K2 closing", f"{n.v_max * (1 - pc['done_fraction']):.2f} V", "<= 5 % V_max",
            1 - pc["done_fraction"] <= 0.05 + 1e-9)
        rec("Precharge", f"{pc['id']} DC-DCs held OFF (remote pin) during precharge", "yes" if pc["dcdc_inhibit"] else "no",
            "required: DDR UVLO turn-on 33.6 V would load the RC", pc["dcdc_inhibit"])

    # ================================================================ regen
    rg = d["regen"]
    hi = min(rg["v_dcdc_ovp_min"], rg["v_motor_ovp"])
    rec("Regen (24 V arm buses)", "Clamp threshold window", f"{rg['v_clamp_on']} V",
        f"> {rg['v_dcdc_set'] + 1:.1f} V and < {hi} V (min of DDR OVP {rg['v_dcdc_ovp_min']} V, Damiao 24 V OVP {rg['v_motor_ovp']} V)",
        rg["v_dcdc_set"] + 1 <= rg["v_clamp_on"] < hi)
    e_cap = 0.5 * rg["c_bus_uf_per_arm"] * 1e-6 * (rg["v_clamp_on"] ** 2 - rg["v_dcdc_set"] ** 2)
    rec("Regen (24 V arm buses)", "Energy bus capacitance can absorb (24 -> 27.5 V)", f"{e_cap:.2f} J vs {rg['e_regen_j_per_arm']} J per stop",
        "", None, "capacitance alone insufficient -> active clamp required" if e_cap < rg["e_regen_j_per_arm"] else "capacitance sufficient")
    cl = comp[rg["clamp_component"]]["ratings"]
    p_cl = rg["v_clamp_on"] ** 2 / cl["r_ohm"]
    rec("Regen (24 V arm buses)", "Clamp absorption at threshold", f"{p_cl:.0f} W", f">= {rg['p_regen_peak_w_per_arm']} W regen peak per arm",
        p_cl >= rg["p_regen_peak_w_per_arm"])
    rec("Regen (24 V arm buses)", "Clamp resistor energy per stop", f"{rg['e_regen_j_per_arm']} J", f"<= {cl['e_pulse_j']} J", rg["e_regen_j_per_arm"] <= cl["e_pulse_j"])
    pav = rg["e_regen_j_per_arm"] * rg["stops_per_min"] / 60
    rec("Regen (24 V arm buses)", f"Clamp average at {rg['stops_per_min']} hard stops/min", f"{pav:.1f} W", f"<= {cl['p_cont_w']} W", pav <= cl["p_cont_w"])

    # ================================================================ autonomy
    tr = d.get("tracer")
    has_tr = bool(tr)
    if not has_tr:   # base with its own battery and charger, not fed from our pack (e.g. MiR250)
        tr = {"v_nom": 0, "ah": 0, "usable_dod": 0}
    eta_tc = comp[tr["charger_component"]]["ratings"]["eta"] if has_tr else 1.0
    e_pack = n.e_nom * b["usable_dod"] + (d["buffer"]["e_wh"] * d["buffer"]["usable"] if d.get("buffer") else 0.0)
    e_tr = tr["v_nom"] * tr["ah"] * tr["usable_dod"]
    conv_of = {c["out_bus"]: c for c in n.conv.values()}
    prof_out = {}
    for pr in d["profiles"]:
        p_pack = p_tr = 0.0
        for l in n.load.values():
            p = pr["p_avg"].get(l["id"], l["p_typ_w"])
            if l["bus"] == "T24":
                p_tr += p
            elif l["bus"] in conv_of:
                p_pack += p / conv_of[l["bus"]]["eta"]
            else:
                p_pack += p
        h_pack, h_tr = e_pack / p_pack, (e_tr / p_tr if p_tr else float("inf"))
        if has_tr and tr.get("transfer") == "base_to_pack":
            # base battery feeds its own loads and tops up our pack through the isolated charger (eta)
            h_comb = (e_tr * eta_tc + e_pack) / (p_tr * eta_tc + p_pack)
        else:
            h_comb = (e_pack + e_tr * eta_tc) / (p_pack + p_tr / eta_tc)
        h_sys = min(h_comb, h_pack + 99 if p_tr == 0 else h_comb)
        prof_out[pr["id"]] = (p_pack, p_tr, h_pack, h_tr, h_comb)
        rec("Autonomy", f"{pr['id']} {pr['desc']}",
            (f"pack {p_pack:.0f} W -> {h_pack:.1f} h; {tr.get('label', 'Tracer')} {p_tr:.0f} W -> {h_tr:.1f} h; combined {h_comb:.1f} h" if has_tr
             else f"{p_pack:.0f} W from {e_pack:.0f} Wh -> {h_pack:.1f} h"),
            f">= {pr['target_h']} h" + (" (combined, with balancing)" if has_tr else ""), h_sys >= pr["target_h"],
            (d.get("autonomy_note") or f"usable pack {e_pack:.0f} Wh, Tracer {e_tr:.0f} Wh; Tracer topped up from pack via isolated charger (eta {eta_tc})"
             if has_tr else d.get("autonomy_note", f"usable pack {e_pack:.0f} Wh; base has its own battery (not counted)")))

    # ================================================================ charging
    if "charging" not in d:
        oem = d.get("oem_dock", {})
        e_used = n.e_nom * b["usable_dod"]
        if oem.get("p_w") and has_tr and tr.get("transfer") == "base_to_pack":
            p_net = oem["p_w"] - oem.get("hotel_w", 0)
            t_sys = (e_tr + e_used / eta_tc) / p_net
            p_c = comp[tr["charger_component"]]["ratings"]
            t_c = e_used / (p_c["i_out_a"] * p_c.get("v_out_v", 54.0))
            t_full = max(t_sys, t_c)
            rec("Charging", "Dock power available to the whole robot", f"{oem['p_w']} W - hotel {oem.get('hotel_w', 0)} W = {p_net} W", "", None, oem.get("note", ""))
            rec("Charging", f"Full recharge of base ({e_tr:.0f} Wh) + our pack ({e_used:.0f} Wh via the {p_c['i_out_a']} A charger) on the one dock",
                f"{t_full:.1f} h (energy limit {t_sys:.1f} h, charger limit {t_c:.1f} h)", f"<= {oem.get('target_h', 4)} h",
                t_full <= oem.get("target_h", 4))
            rec("Charging", "Opportunity charge 20 -> 80 % of both batteries", f"{0.6 * t_full * 60:.0f} min", f"<= {oem.get('target_20_80_min', 120)} min",
                0.6 * t_full * 60 <= oem.get("target_20_80_min", 120))
        elif oem.get("p_w"):
            p_net = oem["p_w"] - oem.get("hotel_w", 0)
            rec("Charging", "Full recharge through the base manufacturer's dock (usable energy)", f"{e_used / p_net:.1f} h",
                f"<= {oem.get('target_h', 4)} h", e_used / p_net <= oem.get("target_h", 4), oem.get("note", ""))
        else:
            rec("Charging", "OEM dock", "no data", "", None, oem.get("note", ""))
        ch = None
    else:
        ch = d["charging"]
    if ch is not None:
        dk = comp[ch["dock_charger_component"]]["ratings"]
        i_dock = min(dk["i_out_a"], dk["p_out_w"] / ch["cv_v"])
        p_dock = i_dock * ch["cv_v"]
        rec("Charging", "Dock charge current vs cell / BMS", f"{i_dock:.1f} A = {i_dock / n.ah:.2f} C",
            f"<= {b['cell']['c_charge']} C and BMS {bms['i_charge_a']} A", i_dock / n.ah <= b["cell"]["c_charge"] and i_dock <= bms["i_charge_a"])
        rec("Charging", "Dock contact current", f"{i_dock:.1f} A", f"<= {comp[ch['dock_contact_component']]['ratings']['i_cont_a']} A",
            i_dock <= comp[ch["dock_contact_component"]]["ratings"]["i_cont_a"])
        p_net1 = p_dock - ch["hotel_load_w"]                      # pack only (Tracer waits)
        p_net2 = p_dock - ch["hotel_load_w"] - ch["tracer_charge_w"] / eta_tc
        i1, i2 = p_net1 / (cv - 1.5), p_net2 / (cv - 1.5)         # mean pack voltage during CC ~ 52.5 V
        t_20_80 = 0.6 * n.ah / i1
        s0, s1 = ch["tracer_priority_soc"], ch["cv_start_soc"]
        t_full = s0 * n.ah / i1 + (s1 - s0) * n.ah / i2 + ch["cv_tail_h"]
        rec("Charging", "Net power into pack on the dock", f"{p_net1:.0f} W ({i1:.1f} A) pack-only; {p_net2:.0f} W ({i2:.1f} A) while Tracer charges",
            "", None, f"dock {p_dock:.0f} W - hotel {ch['hotel_load_w']} W - Tracer {ch['tracer_charge_w']} W / {eta_tc}")
        rec("Charging", "Opportunity charge 20 % -> 80 % (Tracer deferred)", f"{t_20_80 * 60:.0f} min", f"<= {ch['target_20_80_min']} min",
            t_20_80 * 60 <= ch["target_20_80_min"])
        rec("Charging", "Full charge 0 -> 100 % (CC, Tracer from 80 %, CV tail)", f"{t_full:.2f} h", f"<= {ch['target_full_h']} h", t_full <= ch["target_full_h"])
        t_tr = tr["v_nom"] * tr["ah"] * 0.8 / ch["tracer_charge_w"] if has_tr else 0.0
        if has_tr:
            rec("Charging", "Tracer battery 10 -> 90 % via onboard charger (10 A)", f"{t_tr:.2f} h", f"<= {ch['target_full_h']} h (AgileX charger: 3 h)", t_tr <= ch["target_full_h"])

    # ================================================================ coffee options
    if "coffee" in d:
        cf = d["coffee"]
        coffee_convs = [c for c in n.conv if n.conv[c]["out_bus"] == "COF24"]
        coffee_loads = [l for l in n.load if n.load[l]["bus"] == "COF24"]
        i_peak_nc = (p_peak - sum(n.conv_in_power(c, "peak") for c in coffee_convs) + n.excl_saving("peak")) / n.v_min
        i_cont_nc = (p_cont - sum(n.conv_in_power(c, "cont") for c in coffee_convs) + n.excl_saving("cont")) / n.v_min
        p2 = next(pr for pr in d["profiles"] if pr["id"] == "P2")
        p2_nc = prof_out["P2"][0] - sum(p2["p_avg"].get(l, 0) for l in coffee_loads) / (n.conv[coffee_convs[0]]["eta"] if coffee_convs else 1)
        base_main = (i_cont_nc, i_peak_nc)
        f0 = comp[n.fuse["F0"]["component"]]["ratings"]["in_a"]
        w01 = n.br["W01"]
        iz_main = d["wiring"]["ampacity_table"][w01["method"]][float(w01["csa_mm2"])] * interp(d["wiring"]["ambient_correction"], w01["ambient_c"])
        for o in cf["options"]:
            p_dc = o["machine_w"] / o["eta_conv"] if o["machine_w"] else 0.0
            i_dc = p_dc / n.v_min
            i_excl = sum(n.load[l]["p_peak_w"] for g in d.get("exclusive", []) for l in g.get("loads", [])) / n.v_min
            i_all = i_peak_nc + i_dc - min(i_dc, i_excl)      # Tracer charging paused while brewing (energy interlock)
            wh_pack = o["wh_per_cup"] / o["eta_conv"] if o["wh_per_cup"] else 0.0
            cups = e_pack / wh_pack if wh_pack else float("inf")
            p_serv = p2_nc + wh_pack * cf["cups_per_hour_service"] + o["idle_w"]
            h_serv = (e_pack + e_tr * eta_tc) / (p_serv + prof_out["P2"][1] / eta_tc)
            main_cont = base_main[0] + i_dc
            f0_need = 1.25 * main_cont
            ok_peak = i_all <= min(bms["i_peak_a"], cell["c_pulse"] * n.ah)
            ok_opt = ok_peak and f0_need <= f0
            is_def = o["id"] == cf["default"]
            rec("Coffee options", f"{o['id']}: {o['desc']}" + (" [DEFAULT]" if is_def else " [alternative: " + ("feasible" if ok_opt else "NOT feasible as-is") + "]"),
                f"DC {p_dc:.0f} W ({i_dc:.1f} A); all-peak {i_all:.0f} A = {i_all / n.ah:.2f} C; {wh_pack:.1f} Wh/cup from pack; "
                f"P2 + {cf['cups_per_hour_service']} cups/h -> {h_serv:.1f} h",
                "all-peak within BMS/cell pulse; main fuse/cable unchanged", ok_opt if is_def else None,
                f"main cont {main_cont:.1f} A needs F0 >= {f0_need:.0f} A (have {f0} A, cable Iz {iz_main:.0f} A)"
                + ("" if f0_need <= f0 else " -> upsize F0 and W01") + ("" if ok_peak else " -> needs brew/arm interlock")
                )

    # ================================================================ motors (per joint) and power scenarios
    for mt in d.get("motors", []):
        w_r = (mt["tau_rated"] * mt["w_rated"] + 1.5 * mt["i_rated"] ** 2 * mt["r_ph"]) / mt["eta_drv"]
        w_p = (mt["tau_peak"] * mt["w_rated"] * 0.5 + 1.5 * mt["i_peak"] ** 2 * mt["r_ph"]) / mt["eta_drv"]
        mt["_w_r"], mt["_w_p"] = w_r, w_p
        rec("Power table: motors (per joint)", f"{mt['model']} x{mt['qty_per_arm']} per arm ({mt['joints']})",
            f"rated {w_r:.0f} W, peak {w_p:.0f} W per joint", "", None,
            f"rated: {mt['tau_rated']} Nm at {mt['w_rated']:.1f} rad/s + 1.5*{mt['i_rated']}^2*{mt['r_ph']} ohm; peak: {mt['tau_peak']} Nm at half speed + "
            f"1.5*{mt['i_peak']}^2*R; drive eta {mt['eta_drv']} | {mt['source']}")
    if d.get("motors"):
        s_r = sum(m["_w_r"] * m["qty_per_arm"] for m in d["motors"])
        s_p = sum(m["_w_p"] * m["qty_per_arm"] for m in d["motors"])
        env = d["arm_envelope"]
        rec("Power table: motors (per joint)", "Sum of all joints of one arm at datasheet rating / peak", f"{s_r:.0f} W / {s_p:.0f} W",
            f"design envelope {env['cont_w']} W cont / {env['peak_w']} W peak per arm", None,
            "joints never all reach rating together; the envelope (OpenArm reference PSU 24 V 15 A, 2 PSUs for heavy payload) is ENFORCED by Damiao current limits + DC-DC current limit")
    for l in (n.load.values() if d.get("power_table") else []):
        bus = n.bus[l["bus"]]
        src = l.get("source", "")
        src = d["sources"].get(src, src) if src else "ASSUMED"
        if l.get("assumed"):
            src = (src + " (ASSUMED)") if src != "ASSUMED" else "ASSUMED"
        duty = {pr["id"]: pr["p_avg"].get(l["id"], l["p_typ_w"]) for pr in d["profiles"]}
        rec("Power table: every load", f"{l['id']}: {l['desc']}", f"{bus['v_nom']} V ({l['bus']}): typ {l['p_typ_w']} / cont {l['p_cont_w']} / peak {l['p_peak_w']} W ({l.get('peak_s', 1)} s)",
            "avg per profile: " + ", ".join(f"{k} {v:.0f} W" for k, v in duty.items()), None, src)
    if d.get("power_table"):
        for c in n.conv.values():
            ob = n.bus[c["out_bus"]]
            po = n.bus_power(c["out_bus"], "cont")
            pt = n.bus_power(c["out_bus"], "typ")
            rec("Power table: DC-DC losses", f"{c['id']} {comp[c['component']]['mpn']} -> {ob['id']}",
                f"typ {pt:.0f} W out -> {pt / c['eta']:.0f} W in (loss {pt / c['eta'] - pt:.1f} W); max sustained {po:.0f} W out -> loss {po / c['eta'] - po:.0f} W",
                f"eta {c['eta']}", None, "")
    for sc in d.get("scenarios", []):
        p_pk = 0.0
        p_bs = 0.0
        notes = []
        for lid, kind in sc["pack_loads"].items():
            l = n.load[lid]
            w = l[f"p_{kind}_w"] if isinstance(kind, str) else float(kind)
            conv = conv_of.get(l["bus"])
            p_pk += w / (conv["eta"] if conv else 1.0)
        for lid, kind in sc.get("base_loads", {}).items():
            l = n.load[lid]
            p_bs += l[f"p_{kind}_w"] if isinstance(kind, str) else float(kind)
        i_pk = p_pk / n.v_min
        lim_p = min(bms["i_peak_a"], cell["c_pulse"] * n.ah) if sc.get("short") else min(bms["i_cont_a"], cell["c_cont"] * n.ah)
        ok_p = i_pk <= lim_p
        ok_b = True
        bl = ""
        if sc.get("base_loads"):
            bb = d["base_battery"]
            i_b = p_bs / bb["v_min"]
            lim_b = bb["c_pulse"] * bb["ah"] if sc.get("short") else bb["c_cont"] * bb["ah"]
            ok_b = i_b <= lim_b
            bl = f"; base battery {p_bs:.0f} W = {i_b:.1f} A ({i_b / bb['ah']:.2f} C) vs {lim_b:.0f} A [A]"
        rec("Power scenarios: do we have the watts?", f"{sc['id']} {sc['desc']}",
            f"our pack {p_pk:.0f} W = {i_pk:.1f} A ({i_pk / n.ah:.2f} C) vs {lim_p:.0f} A" + bl,
            "YES if within limits", (None if sc.get("info_only") else ok_p and ok_b),
            ("(info) would be " + ("YES" if ok_p and ok_b else "NO") + " - " if sc.get("info_only") else "") + sc.get("requires", ""))

    # ================================================================ safety
    for sf in d["safety"]["functions"]:
        pfh, parts, unknown = 0.0, [], []
        for el in sf["chain"]:
            if el.get("pfhd") is None:
                unknown.append(el["name"])
                continue
            pfh += el["pfhd"]
            parts.append(f"{el['name']}: {el['pfhd']:.1e}" + (" (assumed)" if el.get("assumed") else ""))
        lim = 1e-6 if sf["plr"] == "d" else 1e-7
        ok = (pfh < lim) and not unknown
        rec("Safety functions (ISO 13849-1)", f"{sf['id']} {sf['desc']} - PLr {sf['plr']}, Cat {sf['cat']}",
            f"PFHd {pfh:.2e} /h" + (" + UNRATED element" if unknown else ""), f"< {lim:.0e} /h, all elements rated", ok,
            "; ".join(parts) + ("; UNRATED: " + ", ".join(unknown) if unknown else ""))

    # ================================================================ BOM
    tot = sum(c.get("price_eur", 0) * c.get("qty", 1) for c in d["components"])
    rec("BOM", "Electrical + safety BOM (robot + dock; excludes arms, Jetson, Tracer, cameras)", f"EUR {tot:,.0f}", "", None,
        "indicative, excl. VAT; includes 2 scanners (EUR 4,600) and PNOZ")

    write_md(d, path_md)
    nf = sum(1 for r in results if r[4] == "FAIL")
    print(f"{len(results)} checks: {sum(1 for r in results if r[4] == 'PASS')} PASS, {nf} FAIL, "
          f"{sum(1 for r in results if r[4] == 'INFO')} INFO -> {path_md}")
    for r in results:
        if r[4] == "FAIL":
            print("  FAIL |", r[0], "|", r[1], "|", r[2], "|", r[3])
    return nf


def write_md(d, path_md):
    np_, nf, ni = (sum(1 for r in results if r[4] == s) for s in ("PASS", "FAIL", "INFO"))
    out = ["# Giorgio electrical design - automated checks", "",
           f"Generated by `calc.py` from `netlist.yaml` (design rev {d['meta']['revision']}). Re-run: `python3 calc.py`.", "",
           f"**{np_} PASS, {nf} FAIL, {ni} INFO.**", "",
           "Inputs flagged `assumed: true` in the netlist are engineering estimates or recalled values, not verified datasheet data. "
           "They are listed in ARCHITECTURE.md section 13. A PASS that depends on them is only as good as the assumption.", ""]
    sec = None
    for s, item, val, lim, st, note in results:
        if s != sec:
            out += ["", f"## {s}", "", "| Check | Value | Limit | Result | Note |", "|---|---|---|---|---|"]
            sec = s
        badge = {"PASS": "PASS", "FAIL": "**FAIL**", "INFO": "info"}[st]
        out.append(f"| {item} | {val} | {lim} | {badge} | {note} |".replace("\n", " "))
    Path(path_md).write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    y = sys.argv[1] if len(sys.argv) > 1 else HERE / "netlist.yaml"
    md = sys.argv[2] if len(sys.argv) > 2 else HERE / "CHECKS.md"
    sys.exit(1 if main(y, md) else 0)
