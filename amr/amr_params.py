"""Giorgio AMR (own base) - all dimensions in mm / kg, base frame as cad/: origin on the floor at the base centre,
x forward, y left, z up.  Every purchased value carries a tag:
  SOURCED   = manufacturer datasheet/page (URL in SOURCES below)
  SECONDARY = distributor / catalogue snippet
  ESTIMATE  = our envelope, to be replaced with the manufacturer CAD before release
Rev B4 (2026-10-05): CERTAINTY.md findings F1-F5 and GAP fixes (CAD_REV_B4.md): SWD 125 at its documented size (L 196 mm coaxial,
7.0 kg, manual p.27-28), drive tunnels E43 (SWD out of the bay air, F3), centre bay rearranged around the coaxial drives, deck
doubler A09 under the column foot (G-19), PCAN at its real size, NPB-750 charger in the dock, top speed 1.1 m/s (G-04).
Rev B3 (2026-10-05): sprung D80 castor suspension in the spine/battery gaps (CASTOR_SUSPENSION.md), DIN layout reconciled with
electrical/din_layout.md, LYNK II at its real size (CAD_REV_B3.md).
Rev B2 (2026-10-05): batteries lying on their side with the top cover outward + keep-outs (CAD_REV_B2.md).
Rev B (2026-10-05, owner decision): NO waist yaw joint. The top deck IS the superstructure flange: deck top at z = 353 mm,
the same height as the old adapter plate (cad/params.py AD_Z1), so the superstructure, the arm poses and the simulations
stay valid without changes. The electronics that sat on the old adapter plate now live inside the base (centre bay).
"""

SOURCES = {
    "swd125": "https://www.ez-wheel.com/en/safety-wheel-drive-swd-125",
    "swd_manual": "https://www.ez-wheel.com/storage/upload/pdf/swd-products-v20x-03112023-user-manual-en-0-0.pdf",
    "swd_price": "https://www.generationrobots.com/en/404239-swd-125-safety-wheel-drive.html",
    "actilink_jp": "https://www.synapticon.com/en/products/actilink-jp",
    "actilink_shop": "https://catalog.synapticon.com/shop/actilink-actuators-actilink-jp-15/actilink-jp-circulo-32-sample-2724",
    "thk_ru": "https://www.thk.com/jp/en/products/cross_roller_ring/cross_roller_ring/ru/",
    "twisterband": "https://www.igus.eu/info/energy-chains-twisterband",
    "nanoscan3": "https://www.sick.com/media/pdf/0/80/980/dataSheet_NANS3-CAAZ30AN1_1100334_en.pdf",
    "flexisoft_moc": "https://www.sick.com/ag/en/products/safety/safe-motion-monitoring-and-control/flexi-soft-drive-monitor/c/g555813",
    "robopad": "https://docs.galco.com/techdoc/rbtq/robopads_dat.pdf",
    "ddr480": "https://www.meanwell.com/Upload/PDF/DDR-480/DDR-480-SPEC.PDF",
}

# ------------------------------------------------------------------ envelope
L, W = 780.0, 560.0                 # body plan (covers); swept turning diameter = 2*hypot(390, 280) - chamfers
X0, X1, Y0, Y1 = -L / 2, L / 2, -W / 2, W / 2
CHAMF = 95.0                        # 45 deg corner chamfers (scanners sit in two of them)
GROUND = 32.0                       # underside of the floor pan (ground clearance; indoor, thresholds <= 20 mm)
PAN_T = 5.0                         # floor pan S355MC 5 mm, laser cut (low, heavy = ballast)
PAN_Z0, PAN_Z1 = GROUND, GROUND + PAN_T
DECK_T = 15.0                       # top deck EN AW-6082-T6 15 mm (rev B: is the column-foot flange; 10 mm deflected 1.49 mm > L/500, CALC)
DECK_Z1 = 353.0                     # = superstructure flange (old AD_Z1)
DECK_Z0 = DECK_Z1 - DECK_T
COVER_T = 2.0                       # covers EN AW-5754 2 mm, powder coated

# ------------------------------------------------------------------ drive: ez-Wheel SWD 125, gear 4:1, brake (EW2A-125HN04B)
WHEEL_D, WHEEL_W = 125.0, 49.7      # SOURCED D125 (datasheet); wheel width 49.7 +-0.6 (SWD manual v2.0.2 p.27 fig. 11)
WHEEL_Y = 232.0                     # wheel centre |y| -> track 464 mm
# rev B4 (F4): the SWD 125 is a coaxial hub drive: wheel + gearbox + motor + electronics + brake on the wheel axis.
# SOURCED SWD manual v2.0.2 p.28 table: 1-stage gearbox (G 111) with external brake: "Dim L 196 mm", "Weight 7 kg" (+-10 %);
# L runs from the wheel outer face to the brake end along the axle. Cross-section ESTIMATE from the p.27-28 drawings and the
# p.20 end-face view: housing height 118 mm -> modelled as a coaxial cylinder D 118 (below the D 125 tyre, so the tyre always
# meets a step first). Connectors (I/O M12-A 12p, 24 VDC M12-L, CAN M12-A, USB M8) are on the inboard end face (manual p.20):
# 40 mm axial keep-out for angled M12 plugs. Vendor STEP to confirm.
SWD_L = 196.0                       # SOURCED (manual p.28, 1-stage + brake)
SWD_BODY_D = 118.0                  # ESTIMATE (manual p.27 end view '118')
SWD_CONN_KO = 40.0                  # ESTIMATE angled M12 plugs + cable bend on the inboard end face
SWD_MASS = 7.0                      # SOURCED manual p.28 "7" kg (1-stage + brake) and datasheet "7 kg with brake"
SWD_Y_IN = WHEEL_Y + WHEEL_W / 2 - SWD_L     # 60.85: inboard end face |y|
SWD = dict(load_kg=250.0, T_nom=7.9, T_peak=13.0, rpm_nom=380.0, P_nom=200.0, V=24.0, price=2333.0)   # SOURCED / SECONDARY price
SUSP = ("rev B3: rigid drive wheels + 4 sprung D80 castors (CASTOR_SUSPENSION.md): each castor rides on a carriage guided by a "
        "HIWIN MGN15R rail + 2 MGN15H blocks on the spine inner face, sprung by 2 x Gutekunst D-313J-02 (k 28.34 N/mm, F_inst 76 N), "
        "travel -2.5 (rubber droop stop) / +17 mm (PU pad on the tower roof underside)")

# ------------------------------------------------------------------ casters (4, corners): Blickle L-ALST 80K on a sprung carriage (rev B3)
# SOURCED blickle.com/product/l-alst-80k-754464 (docs/fonti/Blickle_L-ALST_80K_754464_product_page_2026-10-05.txt):
# D 80, width 30, 200 kg @ 4 km/h, static 500 kg, H 102, plate 100 x 85, holes 80 x 60 d9, offset F 38, 0.7 kg.
CASTER_D, CASTER_W, CASTER_H = 80.0, 30.0, 102.0   # SOURCED (castor only: floor -> top of the castor plate)
CASTER_PLATE = (100.0, 85.0)                       # SOURCED
CASTER_PLATE_T = 4.0                               # ESTIMATE (Blickle CAD behind login)
CASTER_TRAIL = 38.0                                # SOURCED offset F
CASTER_SWIVEL_R = 79.4                             # ESTIMATE = hypot(F + D/2, w/2) (Blickle does not publish it; Tente's published radii match)
CASTER_FORK_R = 50.0                               # ESTIMATE fork envelope radius, z 80..98 (castor frame)
CASTER_XY = (275.0, 180.0)                         # swivel axis (CASTOR_SUSPENSION.md P1; (280, 198) never fitted)
CASTER_MASS = 0.7                                  # SOURCED castor only (carriage, blocks, springs are separate CAD parts)
CASTER_LOAD_KG = (200.0, 500.0)                    # SOURCED dynamic @ 4 km/h, static
SUSP_K = 2 * 14.172                                # N/mm per castor, 2 x D-313J-02 R 14.172 N/mm (SOURCED Gutekunst datasheet)
SUSP_F_INST = 76.0                                 # N per castor, set per corner on a scale with the B1 slots (+-3 mm)
SUSP_TRAVEL = (-2.5, 17.0)                         # mm: droop stop (rubber buffer) / bump stop (PU pad -> roof underside)
SPRING = dict(d=3.6, De=31.6, Di=24.4, L0=53.9, Ln=30.78, Fn=327.711, Lndyn=32.67, Fndyn=300.878, R=14.172, price_17=1.66, price_1=12.37)   # SOURCED D-313J-02
MGN15H = dict(H=16.0, W=32.0, L=58.8, C=6.37, C0=9.11, MR=73.5, MP=57.82, MY=57.82, mass=0.092)   # SOURCED HIWIN G99TE24-2410 p.91 (kN, N.m, kg)
MGN15R = dict(WR=15.0, HR=10.0, P=40.0, E=15.0, L=190.0, kg_m=1.06)                                  # SOURCED, L = 15 + 4 x 40 + 15
TOWER_ROOF = (128.0, 134.0)                        # roof 6 mm S355MC: underside 128 = 102 + 6 + 3 + 17 (bump travel); top 134 = scanner seat
SPINE_NOTCH = (202.0, 262.0, 37.0, 128.0)          # |x| range, z range of the spine-end notch (swivel space + carriage tongue)
PAN_CUT_R = 86.0                                   # pan corner cut about the castor axis

# ------------------------------------------------------------------ batteries: 2x Discover AES PRO DLP-GC2-48V in parallel (front + rear, lying)
# SOURCED https://discoverbattery.com/products/search/dlp-gc2-48v : LFP 51.2 V 30 Ah 1.54 kWh, 58 A cont / 90 A 3 s, 14 kg,
# case 260 L x 180 W x 254 H mm, IP67, IEC 62619 + UL 2271 + CE + UN 38.3; each pack < 2 kWh (EU 2023/1542 not triggered)
# rev B2 (manual 805-0027 Rev N s.9.2 p.10, VERIFICATION D1): lying is allowed, never upside down, >= 50 mm free above the
# TOP COVER, over-the-top hold-downs. Each pack lies on its side: pack height axis (254) along x with the top cover facing
# OUTWARD (+x front pack, -x rear pack), width 180 along y, length 260 vertical. Keys: Lx/Wy/H = extents along x/y/z in the CAD.
BATT = dict(Lx=254.0, Wy=180.0, H=260.0, mass=14.0, V=51.2, Ah=30.0, kWh=1.54, I_cont=58.0, I_peak=90.0, price_usd=1009.0,
            name="Discover AES PRO DLP-GC2-48V (LFP 51.2 V 30 Ah)")
BATT_X_IN = 80.0                    # inner (bottom-of-pack) face |x|; top cover at |x| = 334, keep-out to 384 < cover inner face 388
BATT_XS = (BATT_X_IN + BATT["Lx"] / 2, -(BATT_X_IN + BATT["Lx"] / 2))   # pack centres (front, rear) = +-207
BATT_Z0 = 40.0                      # on the 3 mm EPDM pad (pan top 37)
BATT_TOP_KO = 50.0                  # SOURCED 805-0027 s.9.2: >= 50 mm free above the top cover

# ------------------------------------------------------------------ converter installation rule (rev B2)
# SOURCED Mean Well DDR-120/240/480 installation manual p.2 and DRDN20/40 manual: vertical only, input terminals at the bottom,
# 5 mm free left/right, 40 mm above, 20 mm below (also applied to DDR-60). Modelled as invisible keep-out solids.
CONV_KO = dict(above=40.0, below=20.0, side=5.0)
DDR480 = (85.5, 125.2, 129.2)       # (width x, height z, depth) SOURCED DDR-480 spec
DDR240 = (40.0, 125.2, 113.5)       # SOURCED DDR-240-SPEC "40*125.2*113.5mm (W*H*D)"
DDR120 = (32.0, 125.2, 102.0)       # SOURCED
DDR60 = (52.5, 90.0, 54.5)          # SOURCED DDR-60 spec (VERIFICATION M9)
DRDN40 = (55.0, 125.2, 100.0)       # SOURCED DRDN40-SPEC "55*125.2*100mm (W*H*D)" (rev B2 CAD had 90 mm height)
DSR50 = (94.0, 41.0, 35.0)          # maxon DSR 50/5, plate mount, any orientation (VERIFICATION MX1)

# DIN rail heights (rail centre z). Side bays: converters on the LOW rails (pan + 20 mm keep-out below), everything that is
# not a converter on the HIGH rails above the converter keep-outs; the MID rail (|x| < 95, above the SWD housing) carries
# tall non-converters and one DRDN40. Corner rails (spine / bracket A06) carry one converter above a castor tower.
Z_RAIL_LO = 120.0                   # DDR-480 z 57.4..182.6, keep-out 37.4..222.6
Z_RAIL_MID = 245.0
Z_RAIL_HI = 275.0                   # modules <= 110 mm tall: z >= 220 (PNOZ 224.3..325.7), under the deck (338)
Z_RAIL_CNR_FL, Z_RAIL_CNR_RR = 217.0, 220.0

# ------------------------------------------------------------------ centre bay (between the batteries, inside the spines)
CENTRE_BAY = dict(x0=-78.0, x1=78.0, y=131.0)          # spine inner faces |y| = 131; pack inner faces |x| = 80
Z_CRAIL_LO, Z_CRAIL_HI = 120.0, 274.0                  # centre rails on the spine inner faces
Z_CRAIL = 213.0                                        # rev B4: ONE centre rail per spine face, raised above the drive tunnels (converter keep-out 130.4..315.6)
# rev B4 (F3): drive tunnel E43 = 2 mm 5754 hood around each SWD body: |x| <= 72, top z 127..129, inboard end cap |y| 18..20, outboard
# baffle |y| 205..207 sealing around the body (D 121 hole). Inlet: pan slot under the inboard end (|y| 22..100, open), outlet: tunnel fan
# E44 (60 mm, on the hood in the side bay, |y| 140..200) into the side bay ahead of the bay exhaust fans. The slot |y| 100..207 is
# closed by an EPDM brush strip. The SWD housing therefore sees room air, not bay air (SWD rated 0..+40 C, datasheet 07/2024).
TUNNEL = dict(x=72.0, t=2.0, z_top=129.0, y_end=18.0, y_baffle=205.0, y_inlet=100.0)
Z_RAIL_RMID = 175.0                                    # rev B4: right MID rail segments |x| 32..95 above the tunnel (E57, E55, E5A, E59)
DOUBLER = dict(x0=-160.0, x1=34.0, t=15.0)             # rev B4 (G-19): A09 6082-T6 15 mm doubler under the deck at the column foot, |y| <= 131
CABLE_PASS = (62.0, 0.0, 50.0, 100.0)                 # deck grommet (x, y, lx, ly): base -> superstructure (24 V arm buses, Ethernet, safety loop)
JETSON_BOX = (-318.0, -208.0, -78.0, 32.0, 353.0, 413.0)   # rev B2: on the deck at the rear under cover K06 (old rev A position)
POSTS = [(360.0, 106.0)]                              # rev B3: deck end posts at (+-360, +-106) (30x30, |y| 91..121): outside the swivel keep-outs, 1 mm from
                                                      # the top-cover keep-outs (|y| <= 90) and the rear exhaust fans (|y| >= 122). The RR post is replaced by
                                                      # bracket A07 (a post at (-360, -106) would hit the RoboPad collector E01, y -182..-92)

# ------------------------------------------------------------------ safety scanners (front-right, rear-left corners, as before)
NS3 = dict(W=100.6, D=102.5, H=80.2, plane=50.5, mass=0.67)     # SOURCED housing and scan-plane height
SCAN_Z = 184.5                                                  # scan plane = castor-tower roof 134 + 50.5 (SOURCED plane height)
SCAN_XY = (290.0, 208.0)                                        # scanner centre |x|, |y| (unchanged since rev B; independent of the castor axis)
SCAN_CORNERS = [(1, -1, -45.0), (-1, 1, 135.0)]

# ------------------------------------------------------------------ dock contacts (robot side, rear) Roboteq RoboPad
ROBOPAD = dict(W=90.0, H=56.0, D=42.0, mass=0.3)               # SOURCED RPCOL90-100 (mass ESTIMATE)
NPB750 = (230.0, 158.0, 67.0)       # SOURCED Mean Well NPB-750-SPEC "230*158*67mm (L*W*H)" (dock charger, rev B4: was an NPB-1700 envelope)
PCAN_GW = (22.5, 99.0, 114.5)       # SOURCED PEAK PCAN-Ethernet Gateway DR user manual 2.1.0 p.65 (rev B3 CAD 45 x 100 x 90)
PAD_Z = 120.0
PAD_Y = -137.0                      # rev B2: off-centre (y -182..-92) so the rear top-cover keep-out (|y| <= 90) stays free

# ------------------------------------------------------------------ DIN bays: vertical spine plates at |y| = SPINE_Y carry the deck AND the DIN rails
SPINE_Y, SPINE_T = 137.0, 6.0       # EN AW-6082-T6 6 mm, x -260..260; left bay (+y) = power, right bay (-y) = safety/control
SPINE_X = 262.0
DIN_DEPTH = 128.0                   # max module depth from the spine face (cover inner face at |y| = 278)

# ------------------------------------------------------------------ superstructure parts that stay unchanged (cad/out/stl), by name prefix
KEEP_PREFIX = ("OA_body_link0", "P02", "P16", "P17", "P18", "P19", "P20", "P21", "P22", "P23", "P24", "P25", "P26", "P27",
               "P28", "P29", "P30", "P31", "S01", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "SH02", "SH03", "SH04",
               "SH05", "SH06", "E11", "E12", "E13", "openarm_")
# replaced by the AMR: B00 (Ranger), P01 adapter, P03-P08 battery/e-plates, P09 pods, P11 standoffs, SH01 deck cover,
# E01-E09 (battery and electronics move into the base or onto the waist plate), S02 scanners (integrated in the base)

# ------------------------------------------------------------------ rev B4 module envelopes (w along the rail, h, depth)
NET1_DIMS = (22.5, 140.4, 92.4)     # SOURCED Phoenix FL SWITCH 1008N 1085256 datasheet: width 22.5, height 140.4, depth 92.4 mm
Z_RAIL_RNET = 164.0                 # rev B4: short right rail x 73..97 for NET1 (140.4 mm tall does not fit the HIGH rail under the deck)
JR1_DIMS = (35.0, 75.0, 102.0)      # SOURCED 2x Phoenix EMG 17-OV-TTL/24DC/2 (2943259): 17.5 x 75 x 102 mm each (G-22)
