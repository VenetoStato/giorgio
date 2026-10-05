"""Giorgio AMR (own base) - all dimensions in mm / kg, base frame as cad/: origin on the floor at the base centre,
x forward, y left, z up.  Every purchased value carries a tag:
  SOURCED   = manufacturer datasheet/page (URL in SOURCES below)
  SECONDARY = distributor / catalogue snippet
  ESTIMATE  = our envelope, to be replaced with the manufacturer CAD before release
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
WHEEL_D, WHEEL_W = 125.0, 50.0      # SOURCED D125 PU 80 ShA; width ESTIMATE (CAD behind login)
WHEEL_Y = 232.0                     # wheel centre |y| -> track 464 mm
SWD_BOX = dict(dx=190.0, dy=66.0, dz=135.0)   # ESTIMATE gear+motor+electronics housing inboard of the wheel
SWD_MASS = 6.0                      # ESTIMATE (not published)
SWD = dict(load_kg=250.0, T_nom=7.9, T_peak=13.0, rpm_nom=380.0, P_nom=200.0, V=24.0, price=2333.0)   # SOURCED / SECONDARY price
SUSP = "rigid drive wheels + 4 spring-loaded castors: the castor springs set the load split (drive wheels >= 35 % of weight each on flat floor; castor spring window per CALC.md s.3, rev B: F_inst 74 N, k <= 29.5 N/mm)"

# ------------------------------------------------------------------ casters (4, corners) Blickle LKPA-VPA 100 class; the 2 scanners sit ON two caster towers
CASTER_D, CASTER_H = 100.0, 128.0   # spring-loaded swivel castor D100 class (e.g. Blickle/Tente suspension castors): SECONDARY / ESTIMATE
CASTER_PLATE = (100.0, 85.0)
CASTER_XY = (280.0, 198.0)
TOWER_ROOF = (CASTER_H, CASTER_H + 6.0)    # castor plate under the roof, scanner on top
CASTER_MASS = 1.6

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
DDR240 = (40.0, 125.2, 100.0)       # SOURCED width/height, depth ASSUMED (rev B value)
DDR120 = (32.0, 125.2, 102.0)       # SOURCED
DDR60 = (52.5, 90.0, 54.5)          # SOURCED DDR-60 spec (VERIFICATION M9)
DRDN40 = (55.0, 90.0, 100.0)        # width SOURCED, depth ASSUMED (rev B value)
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
CABLE_PASS = (62.0, 0.0, 50.0, 100.0)                 # deck grommet (x, y, lx, ly): base -> superstructure (24 V arm buses, Ethernet, safety loop)
JETSON_BOX = (-318.0, -208.0, -78.0, 32.0, 353.0, 413.0)   # rev B2: on the deck at the rear under cover K06 (old rev A position)
POSTS = [(320.0, 115.0)]                              # deck end posts at (+-320, +-115): clear of the packs (|y| <= 90), keep-outs and towers

# ------------------------------------------------------------------ safety scanners (front-right, rear-left corners, as before)
NS3 = dict(W=100.6, D=102.5, H=80.2, plane=50.5, mass=0.67)     # SOURCED housing and scan-plane height
SCAN_Z = 184.5                                                  # scan plane = castor-tower roof 134 + 50.5 (SOURCED plane height)
SCAN_CORNERS = [(1, -1, -45.0), (-1, 1, 135.0)]

# ------------------------------------------------------------------ dock contacts (robot side, rear) Roboteq RoboPad
ROBOPAD = dict(W=90.0, H=56.0, D=42.0, mass=0.3)               # SOURCED RPCOL90-100 (mass ESTIMATE)
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
