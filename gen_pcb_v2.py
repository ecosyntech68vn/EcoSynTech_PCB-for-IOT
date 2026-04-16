#!/usr/bin/env python3
"""
EcoSynTech PCB v6.3 — Complete KiCad PCB Generator
Generates: .kicad_pcb with all footprints, traces, vias, zones, silkscreen, edge cuts
"""
import os, uuid, math

OUT = "/tmp/ecosyn-pcb"
PROJ = "EcoSynTech_V6_3_Final"

os.makedirs(f"{OUT}/gerber", exist_ok=True)
os.makedirs(f"{OUT}/manufacturing", exist_ok=True)

# KiCad internal units: 1 inch = 2540000 units, 1mm = 100000 units
MM = 100000.0
MIL = 2540.0

def u(x): return int(x * MM)       # mm to KiCad units
def uid(): return str(uuid.uuid4())

# ═══════════════════════════════════════════════════════════════════════════════
# BOARD PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════
BOARD_W = u(200.0)   # 200mm
BOARD_H = u(150.0)   # 150mm
THICKNESS = u(1.6)   # 1.6mm

# Layer IDs (KiCad 6)
L_FCU, L_BCU = 0, 31
L_FSILK, L_BSILK = 37, 36
L_FMASK, L_BMASK = 39, 38
L_FPASTE, L_BPASTE = 35, 34
L_EDGES = 44
L_DWGS = 40
L_CMTS = 41

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTPRINT LIBRARY
# All footprints with pad definitions
# ═══════════════════════════════════════════════════════════════════════════════

class Footprint:
    def __init__(self, name, ref, val, cx, cy, pads, attrs=None, rot=0):
        self.name = name
        self.ref = ref
        self.val = val
        self.cx = cx; self.cy = cy  # center in mm
        self.pads = pads              # list of (num, cx, cy, w, h, drill, shape)
                                     # shape: "circle", "rect", "oval"
        self.rot = rot
        self.attrs = attrs or {}

    def render(self):
        lines = [
            f'  (footprint "{self.name}"',
            f'    (uuid "{uid()}")',
            f'    (at {self.cx} {self.cy} {self.rot})',
            f'    (property (reference "{self.ref}") (value "{self.val}") (at 0 0 0))',
        ]
        if "smd" in self.attrs:
            lines.append('    (attr smd)')
        for num, px, py, w, h, drill, shape in self.pads:
            shape_code = {"circle": "circle", "rect": "rect", "oval": "oval"}.get(shape, "oval")
            drill_str = f'(drill {drill})' if drill > 0 else ''
            lines.append(f'    (pad "" {shape_code} (at {px} {py} 0) (size {w} {h}) {drill_str} (layers F.Cu B.Cu F.Mask B.Mask))')
        lines.append('  )')
        return '\n'.join(lines)

def fp(name, ref, val, cx, cy, pads, smd=False, **kw):
    attrs = dict(kw)
    if smd:
        attrs["smd"] = True
    return Footprint(name, ref, val, cx, cy, pads, attrs)

# ── PAD GENERATORS ─────────────────────────────────────────────────────────
def pad_tht(x, y, drill, w=1.4, h=1.4, shape="oval"):
    return ("", x, y, w, h, drill, shape)

def pad_smd(x, y, w=1.4, h=1.4):
    return ("", x, y, w, h, 0, "rect")

def pad_smd_circle(x, y, dia=1.4):
    return ("", x, y, dia, dia, 0, "circle")

# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT PLACEMENT — per PCB_LAYOUT_V3.md
# Coordinate system: X 0-200mm (left→right), Y 0-150mm (bottom→top)
# ═══════════════════════════════════════════════════════════════════════════════

# Format: (ref, value, cx_mm, cy_mm, pads, [attrs])
# All coordinates are CENTER of component

FP_LIST = []

def add_fp(fp):
    FP_LIST.append(fp)
    return fp

# ── POWER INPUT (Z1: X:5-50, Y:5-60) ───────────────────────────────────────
add_fp(fp("CONN_5.08_2P", "TB1", "Terminal Block",
    10, 18, [pad_tht(0, -2.54, 1.0, 1.6, 1.6), pad_tht(0, 2.54, 1.0, 1.6, 1.6)]))

add_fp(fp("FUSE_HOLDER_5x20", "F1", "Fuse 2A 250V",
    22, 18, [pad_tht(0, -2.54, 1.0, 1.6, 1.6), pad_tht(0, 2.54, 1.0, 1.6, 1.6)]))

add_fp(fp("GDT", "GDT1", "Bourns 2027-09-B",
    35, 18, [pad_tht(-3.75, 0, 1.0), pad_tht(3.75, 0, 1.0)]))

add_fp(fp("MOV", "MOV1", "14D201K",
    48, 18, [pad_tht(-7.0, 0, 1.0), pad_tht(7.0, 0, 1.0)]))

add_fp(fp("R_2512", "R_SURGE1", "5.6R 2W",
    62, 18, [pad_smd(-2.8, 0, 2.2, 1.35), pad_smd(2.8, 0, 2.2, 1.35)],
    smd=True))

add_fp(fp("INDUCTOR", "L_SURGE1", "22uH 2A",
    75, 18, [pad_tht(-4.0, 0, 1.0, 1.5, 1.5), pad_tht(4.0, 0, 1.0, 1.5, 1.5)]))

add_fp(fp("D_SMB", "D_TVS1", "SMBJ24A",
    90, 18, [pad_smd(-2.4, 0, 1.8, 1.35), pad_smd(2.4, 0, 1.8, 1.35)],
    smd=True))

# P-MOSFET AO4407A SO-8
add_fp(fp("SO-8", "Q_PROTECT", "AO4407A",
    105, 18, [
        pad_smd(-3.81, -1.27, 0.6, 1.27), pad_smd(-1.27, -1.27, 0.6, 1.27),
        pad_smd(1.27, -1.27, 0.6, 1.27), pad_smd(3.81, -1.27, 0.6, 1.27),
        pad_smd(-3.81, 1.27, 0.6, 1.27), pad_smd(-1.27, 1.27, 0.6, 1.27),
        pad_smd(1.27, 1.27, 0.6, 1.27), pad_smd(3.81, 1.27, 0.6, 1.27),
    ], smd=True))

# Gate resistors for Q_PROTECT
add_fp(fp("R_0805", "R_G1", "100k 1%",
    105, 10, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_G2", "100k 1%",
    105, 5, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# Zener DZ_G1
add_fp(fp("D_SOD-123", "DZ_G1", "15V",
    105, 27, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))

# C1 bulk cap 470uF
add_fp(fp("CAP_D8x11.5", "C1", "470uF 25V",
    120, 18, [pad_tht(-5.75, 0, 0.8, 1.6, 1.6), pad_tht(5.75, 0, 0.8, 1.6, 1.6)]))

# C2, C3
add_fp(fp("C_1210", "C2", "1uF 50V",
    130, 12, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_0805", "C3", "100nF 50V",
    130, 23, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── BUCK #1 12V→5V (Z2: X:55-105, Y:5-50) ──────────────────────────────
add_fp(fp("SOIC-8E", "U2_5V", "MP1584EN",
    72, 35, [
        pad_smd(-3.81, -2.54, 0.6, 1.27), pad_smd(-3.81, -1.27, 0.6, 1.27),
        pad_smd(-3.81, 0, 0.6, 1.27), pad_smd(-3.81, 1.27, 0.6, 1.27),
        pad_smd(3.81, -2.54, 0.6, 1.27), pad_smd(3.81, -1.27, 0.6, 1.27),
        pad_smd(3.81, 0, 0.6, 1.27), pad_smd(3.81, 1.27, 0.6, 1.27),
    ], smd=True))

add_fp(fp("C_1210", "CIN_5V1", "22uF 50V",
    60, 42, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_0805", "CIN_5V2", "100nF 50V",
    60, 35, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

add_fp(fp("L_6x6", "L_5V", "10uH 3A",
    83, 35, [pad_tht(-3.0, 0, 1.0, 1.4, 1.4), pad_tht(3.0, 0, 1.0, 1.4, 1.4)]))

add_fp(fp("C_1210", "COUT_5V1", "22uF 16V",
    93, 42, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_1210", "COUT_5V2", "22uF 16V",
    93, 38, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_0805", "COUT_5V3", "100nF 16V",
    93, 34, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

add_fp(fp("R_0805", "R_FB1_5V", "10k 1%",
    82, 28, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_FB2_5V", "52.3k 1%",
    82, 24, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_EN_5V", "100k 1%",
    60, 28, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

add_fp(fp("D_SMA", "D_OUT5V", "SS34",
    90, 50, [pad_smd(-2.4, 0, 1.8, 1.35), pad_smd(2.4, 0, 1.8, 1.35)], smd=True))

# Thermal vias under U2_5V
for tx, ty in [(68, 38), (68, 35), (68, 32), (76, 38), (76, 35), (76, 32)]:
    add_fp(fp("VIA", f"TV_U2_5V_{tx}_{ty}", "",
        tx, ty, [pad_tht(0, 0, 0.4, 0.6, 0.6)]))

# ── BUCK #2 12V→3.3V (Z3: X:110-160, Y:5-50) ───────────────────────────
add_fp(fp("SOIC-8E", "U3_3V3", "MP1584EN",
    112, 35, [
        pad_smd(-3.81, -2.54, 0.6, 1.27), pad_smd(-3.81, -1.27, 0.6, 1.27),
        pad_smd(-3.81, 0, 0.6, 1.27), pad_smd(-3.81, 1.27, 0.6, 1.27),
        pad_smd(3.81, -2.54, 0.6, 1.27), pad_smd(3.81, -1.27, 0.6, 1.27),
        pad_smd(3.81, 0, 0.6, 1.27), pad_smd(3.81, 1.27, 0.6, 1.27),
    ], smd=True))

add_fp(fp("C_1210", "CIN_3V31", "22uF 25V",
    100, 42, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_0805", "CIN_3V32", "100nF 25V",
    100, 35, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

add_fp(fp("L_6x6", "L_3V3", "10uH 2A",
    123, 35, [pad_tht(-3.0, 0, 1.0, 1.4, 1.4), pad_tht(3.0, 0, 1.0, 1.4, 1.4)]))

add_fp(fp("C_1210", "COUT_3V31", "22uF 16V",
    133, 42, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_1210", "COUT_3V32", "22uF 16V",
    133, 38, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_0805", "COUT_3V33", "100nF 16V",
    133, 34, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

add_fp(fp("R_0805", "R_FB1_3V3", "10k 1%",
    122, 28, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_FB2_3V3", "31.6k 1%",
    122, 24, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_EN_3V3", "100k 1%",
    100, 28, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

for tx, ty in [(108, 38), (108, 35), (108, 32), (116, 38), (116, 35), (116, 32)]:
    add_fp(fp("VIA", f"TV_U3_3V3_{tx}_{ty}", "",
        tx, ty, [pad_tht(0, 0, 0.4, 0.6, 0.6)]))

# ── RAIL SPLITTING (Z5: X:5-100, Y:65-115) ───────────────────────────────
add_fp(fp("FB_0805", "FB_ESP", "BLM18PG121SN1",
    58, 47, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_ESP1", "10uF 10V",
    63, 47, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_ESP2", "100nF 10V",
    66, 47, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

add_fp(fp("FB_0805", "FB_ANA", "BLM18PG121SN1",
    58, 67, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_ANA1", "10uF 10V",
    63, 67, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_ANA2", "100nF 10V",
    66, 67, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# POWER_GOOD
add_fp(fp("SOT-23", "U_PWR_GOOD", "MCP809T-315",
    138, 57, [
        pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9),
    ], smd=True))
add_fp(fp("C_0805", "C_PWR_GOOD", "100nF 10V",
    141, 57, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── OR-ING DIODES (Z1-Z2 boundary) ────────────────────────────────────────
add_fp(fp("D_SMA", "D_USB", "SS34",
    20, 35, [pad_smd(-2.4, 0, 1.8, 1.35), pad_smd(2.4, 0, 1.8, 1.35)], smd=True))
add_fp(fp("D_SMA", "D_MAIN", "SS34",
    27, 35, [pad_smd(-2.4, 0, 1.8, 1.35), pad_smd(2.4, 0, 1.8, 1.35)], smd=True))
add_fp(fp("C_1210", "C_SYS1", "47uF 16V",
    35, 35, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))
add_fp(fp("C_0805", "C_SYS2", "100nF 16V",
    40, 35, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── ESP32 MODULE (Z5: X:100-200, Y:55-115) ──────────────────────────────
# ESP32-WROOM-32E module footprint (38-pin)
# Module size: ~18mm × 25mm
add_fp(fp("ESP32-WROOM-32E", "U_ESP32", "ESP32-WROOM-32E",
    165, 57.5,
    [
        # Left side pins (x = -8.97)
        pad_smd(-8.97, -3.81, 0.5, 0.9), pad_smd(-8.97, -2.54, 0.5, 0.9),
        pad_smd(-8.97, -1.27, 0.5, 0.9), pad_smd(-8.97, 0, 0.5, 0.9),
        pad_smd(-8.97, 1.27, 0.5, 0.9), pad_smd(-8.97, 2.54, 0.5, 0.9),
        pad_smd(-8.97, 3.81, 0.5, 0.9), pad_smd(-8.97, 5.08, 0.5, 0.9),
        pad_smd(-8.97, 6.35, 0.5, 0.9), pad_smd(-8.97, 7.62, 0.5, 0.9),
        pad_smd(-8.97, 8.89, 0.5, 0.9), pad_smd(-8.97, 10.16, 0.5, 0.9),
        pad_smd(-8.97, 11.43, 0.5, 0.9), pad_smd(-8.97, 12.7, 0.5, 0.9),
        pad_smd(-8.97, 13.97, 0.5, 0.9), pad_smd(-8.97, 15.24, 0.5, 0.9),
        pad_smd(-8.97, 16.51, 0.5, 0.9), pad_smd(-8.97, 17.78, 0.5, 0.9),
        pad_smd(-8.97, 19.05, 0.5, 0.9),
        # Right side pins (x = 8.97)
        pad_smd(8.97, -3.81, 0.5, 0.9), pad_smd(8.97, -2.54, 0.5, 0.9),
        pad_smd(8.97, -1.27, 0.5, 0.9), pad_smd(8.97, 0, 0.5, 0.9),
        pad_smd(8.97, 1.27, 0.5, 0.9), pad_smd(8.97, 2.54, 0.5, 0.9),
        pad_smd(8.97, 3.81, 0.5, 0.9), pad_smd(8.97, 5.08, 0.5, 0.9),
        pad_smd(8.97, 6.35, 0.5, 0.9), pad_smd(8.97, 7.62, 0.5, 0.9),
        pad_smd(8.97, 8.89, 0.5, 0.9), pad_smd(8.97, 10.16, 0.5, 0.9),
        pad_smd(8.97, 11.43, 0.5, 0.9), pad_smd(8.97, 12.7, 0.5, 0.9),
        pad_smd(8.97, 13.97, 0.5, 0.9), pad_smd(8.97, 15.24, 0.5, 0.9),
        pad_smd(8.97, 16.51, 0.5, 0.9), pad_smd(8.97, 17.78, 0.5, 0.9),
        pad_smd(8.97, 19.05, 0.5, 0.9),
    ], smd=True))

# ESP32 decoupling caps
for i, (x, y) in enumerate([(150, 70), (152, 73), (154, 76)]):
    add_fp(fp("C_0805", f"C_ESP_DEC{i+1}", "100nF 10V",
        x, y, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# Pull-ups
add_fp(fp("R_0805", "R_EN_PU", "10k", 160, 68, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_BOOT_PU", "10k", 163, 68, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_BOOT_OK_PU", "10k", 166, 68, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# Status LEDs (top of ESP32, active-LOW)
for i, (y, name) in enumerate([(50, "LED_PWR"), (53, "LED_WIFI"), (56, "LED_MQTT"), (59, "LED_ERROR")]):
    add_fp(fp("LED_0805", name, "LED",
        155, y, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
    add_fp(fp("R_0805", f"R_LED_{name.split('_')[1]}", "1.5k",
        152, y, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# Series resistors for sensors
add_fp(fp("R_0805", "R_DHT_SER", "100R", 40, 45, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_DS_SER", "100R", 40, 55, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_VSENSE_SER", "1k", 170, 72, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── USB-UART (Z4: X:120-200, Y:5-50) ────────────────────────────────────
add_fp(fp("USB_MICRO_B", "J_USB", "USB Micro-B",
    25, 30, [pad_tht(0, -3.0, 0.8), pad_tht(0, -1.0, 0.8),
              pad_tht(0, 1.0, 0.8), pad_tht(0, 3.0, 0.8),
              pad_smd(-1.5, 0, 1.0, 0.8), pad_smd(1.5, 0, 1.0, 0.8)]))

add_fp(fp("FUSE_PTC", "F_USB", "PTC 500mA",
    32, 30, [pad_tht(-2.0, 0, 0.8), pad_tht(2.0, 0, 0.8)]))

add_fp(fp("D_SMB", "D_TVS_USB", "SMBJ5.0A",
    39, 30, [pad_smd(-2.4, 0, 1.8, 1.35), pad_smd(2.4, 0, 1.8, 1.35)], smd=True))

add_fp(fp("R_1206", "R_USB_LIM", "2.2R",
    46, 30, [pad_smd(-0.8, 0, 1.4, 0.9), pad_smd(0.8, 0, 1.4, 0.9)], smd=True))

add_fp(fp("SOT-23-6", "ESD_USB", "USBLC6-2SC6",
    53, 30, [
        pad_smd(-0.5, -1.27, 0.6, 0.9), pad_smd(-0.5, 0, 0.6, 0.9),
        pad_smd(-0.5, 1.27, 0.6, 0.9), pad_smd(0.5, -1.27, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9), pad_smd(0.5, 1.27, 0.6, 0.9),
    ], smd=True))

# CP2102 QFN-28
add_fp(fp("QFN-28", "U_USB_UART", "CP2102-GMR",
    35, 53,
    [
        pad_smd(-2.25, -2.25, 0.25, 0.5), pad_smd(-2.25, -1.5, 0.25, 0.5),
        pad_smd(-2.25, -0.75, 0.25, 0.5), pad_smd(-2.25, 0, 0.25, 0.5),
        pad_smd(-2.25, 0.75, 0.25, 0.5), pad_smd(-2.25, 1.5, 0.25, 0.5),
        pad_smd(-2.25, 2.25, 0.25, 0.5), pad_smd(-1.5, -2.25, 0.25, 0.5),
        pad_smd(-0.75, -2.25, 0.25, 0.5), pad_smd(0, -2.25, 0.25, 0.5),
        pad_smd(0.75, -2.25, 0.25, 0.5), pad_smd(1.5, -2.25, 0.25, 0.5),
        pad_smd(2.25, -2.25, 0.25, 0.5), pad_smd(2.25, -1.5, 0.25, 0.5),
        pad_smd(2.25, -0.75, 0.25, 0.5), pad_smd(2.25, 0, 0.25, 0.5),
        pad_smd(2.25, 0.75, 0.25, 0.5), pad_smd(2.25, 1.5, 0.25, 0.5),
        pad_smd(2.25, 2.25, 0.25, 0.5), pad_smd(1.5, 2.25, 0.25, 0.5),
        pad_smd(0.75, 2.25, 0.25, 0.5), pad_smd(0, 2.25, 0.25, 0.5),
        pad_smd(-0.75, 2.25, 0.25, 0.5), pad_smd(-1.5, 2.25, 0.25, 0.5),
        pad_smd(-2.25, 2.25, 0.25, 0.5),
        pad_smd(0, 0, 0.5, 0.5),
    ], smd=True))

# Auto-reset transistors
add_fp(fp("SOT-23", "Q_RST", "BC847",
    40, 60, [
        pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9),
    ], smd=True))
add_fp(fp("R_0805", "R_USB_DTR", "1k",
    37, 60, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

add_fp(fp("SOT-23", "Q_BOOT", "BC847",
    40, 65, [
        pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9),
    ], smd=True))
add_fp(fp("R_0805", "R_USB_RTS", "1k",
    37, 65, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── HARDWARE WATCHDOG TPL5010 (Z5) ─────────────────────────────────────────
add_fp(fp("SOT-23-6", "U_WD", "TPL5010DDCT",
    50, 58, [
        pad_smd(-0.5, -1.27, 0.6, 0.9), pad_smd(-0.5, 0, 0.6, 0.9),
        pad_smd(-0.5, 1.27, 0.6, 0.9), pad_smd(0.5, -1.27, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9), pad_smd(0.5, 1.27, 0.6, 0.9),
    ], smd=True))

add_fp(fp("R_0805", "R_WD_RT", "49.9k 1%",
    58, 58, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_WD_DONE_PU", "10k",
    47, 61, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_WD_WAKE", "10k",
    55, 61, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_WD_FILT", "100nF",
    50, 64, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# D_RST BAT54S
add_fp(fp("SOT-23", "D_RST", "BAT54S",
    55, 60, [
        pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9),
    ], smd=True))

# ── RELAY DRIVERS ×4 + POWER LIMITING (Z8: X:5-100, Y:120-145) ───────────
add_fp(fp("R_2512", "R_RELAY_LIM", "0.5R 1W",
    15, 88, [pad_smd(-2.8, 0, 2.2, 1.35), pad_smd(2.8, 0, 2.2, 1.35)], smd=True))

add_fp(fp("CAP_D10x12.5", "C_RELAY_BULK", "1000uF 16V",
    28, 88, [pad_tht(-6.25, 0, 0.8, 1.6, 1.6), pad_tht(6.25, 0, 0.8, 1.6, 1.6)]))

add_fp(fp("D_SMB", "D_RELAY_TVS", "SMBJ5.0A",
    40, 88, [pad_smd(-2.4, 0, 1.8, 1.35), pad_smd(2.4, 0, 1.8, 1.35)], smd=True))

# 4 relay drivers
for i, y in enumerate([93, 110, 127, 144]):
    drv_x = 162
    r_x = 155
    q_x = 148
    add_fp(fp("SOT-23", f"Q_R{i+1}", "S8050",
        q_x, y, [
            pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
            pad_smd(0.5, 0, 0.6, 0.9),
        ], smd=True))
    add_fp(fp("R_0805", f"R_GR{i+1}", "100R",
        r_x, y, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
    add_fp(fp("D_SOD-123", f"D_FLY{i+1}", "1N4148",
        r_x + 12, y, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))
    add_fp(fp("SOT-23", f"R_PD_R{i+1}", "100k",
        q_x - 8, y, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# Relay sockets
for i, y in enumerate([93, 110, 127, 144]):
    relay_x = 175
    add_fp(fp("RELAY_SRD_5V", f"RELAY{i+1}", "SRD-05VDC-SL-C",
        relay_x, y,
        [pad_tht(-3.81, -2.54, 1.0), pad_tht(-3.81, 2.54, 1.0),
         pad_tht(3.81, -2.54, 1.0), pad_tht(3.81, 2.54, 1.0),
         pad_tht(0, -2.54, 1.0)]))

    j_x = 185
    add_fp(fp("CONN_7.62_3P", f"J_R{i+1}", "3P 7.62mm",
        j_x, y,
        [pad_tht(-7.62, -2.54, 1.2), pad_tht(0, -2.54, 1.2), pad_tht(7.62, -2.54, 1.2)]))

# RELAY_EN interlock
add_fp(fp("SOT-23", "D_RELAY_PWR_GOOD", "BAT54S",
    45, 93, [
        pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9),
    ], smd=True))
add_fp(fp("SOT-23", "D_RELAY_BOOT_OK", "BAT54S",
    55, 93, [
        pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9),
    ], smd=True))
add_fp(fp("R_0805", "R_RELAY_EN_PU", "10k",
    65, 93, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_RELAY_EN_PD", "100k",
    65, 88, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── SENSORS (Z7: X:5-50, Y:40-60) ────────────────────────────────────────
# DHT22
add_fp(fp("DHT22_TH", "U_DHT22", "AM2302",
    50, 45, [pad_tht(-2.54, -1.27, 0.7), pad_tht(0, -1.27, 0.7), pad_tht(2.54, -1.27, 0.7)]))
add_fp(fp("CONN_3.81_3P", "J_DHT", "CONN_3.81_3P",
    40, 35, [pad_tht(-3.81, 0, 0.7), pad_tht(0, 0, 0.7), pad_tht(3.81, 0, 0.7)]))
add_fp(fp("R_0805", "R_DHT_PU", "4.7k",
    48, 38, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("D_SOD-123", "D_DHT_ESD", "SMBJ5.0A",
    55, 40, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))

# DS18B20
add_fp(fp("TO-92", "U_DS18B20", "DS18B20",
    50, 55, [pad_tht(-1.27, -2.54, 0.7), pad_tht(0, -2.54, 0.7), pad_tht(1.27, -2.54, 0.7)]))
add_fp(fp("CONN_3.81_3P", "J_DS", "CONN_3.81_3P",
    40, 45, [pad_tht(-3.81, 0, 0.7), pad_tht(0, 0, 0.7), pad_tht(3.81, 0, 0.7)]))
add_fp(fp("R_0805", "R_DS_PU", "4.7k",
    48, 48, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("D_SOD-123", "D_DS_ESD", "SMBJ5.0A",
    55, 50, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))

# ── ADS1115 + ANALOG (Z7: X:80-150, Y:50-70) ─────────────────────────────
add_fp(fp("MSOP-8", "U_ADS", "ADS1115IDGSR",
    82, 53,
    [
        pad_smd(-1.95, -1.5, 0.3, 0.6), pad_smd(-1.95, -0.5, 0.3, 0.6),
        pad_smd(-1.95, 0.5, 0.3, 0.6), pad_smd(-1.95, 1.5, 0.3, 0.6),
        pad_smd(1.95, -1.5, 0.3, 0.6), pad_smd(1.95, -0.5, 0.3, 0.6),
        pad_smd(1.95, 0.5, 0.3, 0.6), pad_smd(1.95, 1.5, 0.3, 0.6),
    ], smd=True))

add_fp(fp("C_0805", "C_ADS_VDD1", "100nF",
    87, 57, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_ADS_VDD2", "10uF",
    90, 57, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# Analog input series + TVS
for i, (x, net) in enumerate([(75, "A0"), (78, "A1"), (81, "A2"), (84, "A3")]):
    add_fp(fp("R_0805", f"R_A{i}_SER", "1k",
        x, 48, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
    add_fp(fp("D_SOD-123", f"D_A{i}_ESD", "SMBJ5.0A",
        x + 3, 48, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))

# J_AIN 6P terminal
add_fp(fp("CONN_3.81_6P", "J_AIN", "CONN_3.81_6P",
    112.5, 60, [
        pad_tht(-12.7, 0, 0.7), pad_tht(-8.89, 0, 0.7), pad_tht(-5.08, 0, 0.7),
        pad_tht(-1.27, 0, 0.7), pad_tht(2.54, 0, 0.7), pad_tht(6.35, 0, 0.7),
    ]))

# ── BATTERY/VIN SENSE ─────────────────────────────────────────────────────
add_fp(fp("CONN_5.08_2P", "J_VBAT", "CONN_5.08_2P",
    190, 28, [pad_tht(0, -2.54, 1.0, 1.6, 1.6), pad_tht(0, 2.54, 1.0, 1.6, 1.6)]))
add_fp(fp("R_0805", "R_VTOP", "100k 1%",
    178, 28, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_VBOT", "33k 1%",
    175, 25, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_VSENSE", "100nF",
    178, 22, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_VSENSE_SER_B", "1k",
    173, 28, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("SOT-23", "D_VSENSE_CLAMP", "BAT54S",
    170, 28, [
        pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
        pad_smd(0.5, 0, 0.6, 0.9),
    ], smd=True))

# ── SOIL SENSOR ────────────────────────────────────────────────────────────
add_fp(fp("CONN_3.81_3P", "J_SOIL", "CONN_3.81_3P",
    40, 55, [pad_tht(-3.81, 0, 0.7), pad_tht(0, 0, 0.7), pad_tht(3.81, 0, 0.7)]))
add_fp(fp("R_0805", "R_SOIL_SER", "1k",
    35, 55, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_SOIL", "100nF",
    32, 55, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("D_SOD-123", "D_SOIL_ESD", "SMBJ5.0A",
    29, 55, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))

# ── I2C + ESD + SERIES (Z6: X:110-145, Y:55-75) ──────────────────────────
add_fp(fp("CONN_3.81_4P", "J_I2C_EXT", "CONN_3.81_4P",
    35, 23, [pad_tht(-5.71, 0, 0.7), pad_tht(-1.9, 0, 0.7), pad_tht(1.9, 0, 0.7), pad_tht(5.71, 0, 0.7)]))
add_fp(fp("CONN_3.81_4P", "J_DEBUG", "CONN_3.81_4P",
    35, 25, [pad_tht(-5.71, 0, 0.7), pad_tht(-1.9, 0, 0.7), pad_tht(1.9, 0, 0.7), pad_tht(5.71, 0, 0.7)]))

add_fp(fp("R_0805", "R_I2C_PU_SCL", "4.7k",
    60, 43, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_I2C_PU_SDA", "4.7k",
    60, 48, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_I2C_SCL_SER", "22R",
    48, 43, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_I2C_SDA_SER", "22R",
    48, 48, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("D_SOD-123", "D_I2C_SCL_ESD", "SMBJ5.0A",
    43, 43, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))
add_fp(fp("D_SOD-123", "D_I2C_SDA_ESD", "SMBJ5.0A",
    43, 48, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))

# BME280 & OLED
add_fp(fp("BME280_I2C", "U_BME280", "BME280",
    127.5, 55, [
        pad_smd(-2.0, -1.5, 0.3, 0.5), pad_smd(-2.0, -0.5, 0.3, 0.5),
        pad_smd(-2.0, 0.5, 0.3, 0.5), pad_smd(-2.0, 1.5, 0.3, 0.5),
        pad_smd(2.0, -1.5, 0.3, 0.5), pad_smd(2.0, -0.5, 0.3, 0.5),
        pad_smd(2.0, 0.5, 0.3, 0.5), pad_smd(2.0, 1.5, 0.3, 0.5),
    ], smd=True))
add_fp(fp("OLED_I2C", "U_OLED", "OLED 0.96",
    145, 55, [
        pad_smd(-3.81, -1.27, 0.3, 0.5), pad_smd(-3.81, 0, 0.3, 0.5),
        pad_smd(-3.81, 1.27, 0.3, 0.5), pad_smd(3.81, -1.27, 0.3, 0.5),
        pad_smd(3.81, 0, 0.3, 0.5), pad_smd(3.81, 1.27, 0.3, 0.5),
    ], smd=True))

# ── MicroSD (Z5: X:130-150, Y:75-90) ────────────────────────────────────
add_fp(fp("MICROSD", "U_SDCARD", "MicroSD Socket",
    140, 80, [
        pad_tht(-5.0, -3.5, 0.6), pad_tht(-2.5, -3.5, 0.6), pad_tht(0, -3.5, 0.6),
        pad_tht(2.5, -3.5, 0.6), pad_tht(5.0, -3.5, 0.6),
        pad_tht(-5.0, 0, 0.6), pad_tht(5.0, 0, 0.6),
        pad_smd(-5.0, 3.5, 1.2, 0.8), pad_smd(5.0, 3.5, 1.2, 0.8),
    ]))
add_fp(fp("R_0805", "R_SD_SCK", "22R",
    134, 83, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_SD_MOSI", "22R",
    134, 80, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_SD_MISO", "22R",
    134, 77, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_SD_CS", "10k",
    134, 74, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("R_0805", "R_SD_DET_PU", "10k",
    134, 71, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
add_fp(fp("C_0805", "C_SD_DEC", "100nF",
    137, 83, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── MCP23017 EXPANDERS (Z6: X:50-100, Y:110-145) ─────────────────────────
add_fp(fp("SSOP-28", "U_EXP1", "MCP23017T-E",
    50, 110,
    [
        pad_smd(-3.2, -2.8, 0.3, 0.6), pad_smd(-3.2, -2.1, 0.3, 0.6),
        pad_smd(-3.2, -1.4, 0.3, 0.6), pad_smd(-3.2, -0.7, 0.3, 0.6),
        pad_smd(-3.2, 0, 0.3, 0.6), pad_smd(-3.2, 0.7, 0.3, 0.6),
        pad_smd(-3.2, 1.4, 0.3, 0.6), pad_smd(-3.2, 2.1, 0.3, 0.6),
        pad_smd(3.2, -2.8, 0.3, 0.6), pad_smd(3.2, -2.1, 0.3, 0.6),
        pad_smd(3.2, -1.4, 0.3, 0.6), pad_smd(3.2, -0.7, 0.3, 0.6),
        pad_smd(3.2, 0, 0.3, 0.6), pad_smd(3.2, 0.7, 0.3, 0.6),
        pad_smd(3.2, 1.4, 0.3, 0.6), pad_smd(3.2, 2.1, 0.3, 0.6),
    ], smd=True))
add_fp(fp("SSOP-28", "U_EXP2", "MCP23017T-E",
    50, 125,
    [
        pad_smd(-3.2, -2.8, 0.3, 0.6), pad_smd(-3.2, -2.1, 0.3, 0.6),
        pad_smd(-3.2, -1.4, 0.3, 0.6), pad_smd(-3.2, -0.7, 0.3, 0.6),
        pad_smd(-3.2, 0, 0.3, 0.6), pad_smd(-3.2, 0.7, 0.3, 0.6),
        pad_smd(-3.2, 1.4, 0.3, 0.6), pad_smd(-3.2, 2.1, 0.3, 0.6),
        pad_smd(3.2, -2.8, 0.3, 0.6), pad_smd(3.2, -2.1, 0.3, 0.6),
        pad_smd(3.2, -1.4, 0.3, 0.6), pad_smd(3.2, -0.7, 0.3, 0.6),
        pad_smd(3.2, 0, 0.3, 0.6), pad_smd(3.2, 0.7, 0.3, 0.6),
        pad_smd(3.2, 1.4, 0.3, 0.6), pad_smd(3.2, 2.1, 0.3, 0.6),
    ], smd=True))

for y in [110, 125]:
    add_fp(fp("C_0805", f"C_EXP{'1' if y==110 else '2'}_DEC1", "100nF",
        y - 5, 115 if y == 110 else 130, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
    add_fp(fp("C_0805", f"C_EXP{'1' if y==110 else '2'}_DEC2", "10uF",
        y - 2, 115 if y == 110 else 130, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))

# ── EXPANSION RELAYS 5-8 (Z10 right: X:150-195, Y:120-145) ────────────────
for i, y in enumerate([93, 110, 127, 144]):
    drv_x = 148
    add_fp(fp("SOT-23", f"Q_R{i+5}", "S8050",
        drv_x, y, [
            pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
            pad_smd(0.5, 0, 0.6, 0.9),
        ], smd=True))
    add_fp(fp("R_0805", f"R_GR{i+5}", "100R",
        drv_x + 7, y, [pad_smd(-0.5, 0, 0.8, 0.5), pad_smd(0.5, 0, 0.8, 0.5)], smd=True))
    add_fp(fp("D_SOD-123", f"D_FLY{i+5}", "1N4148",
        drv_x + 14, y, [pad_smd(-0.7, 0, 0.8, 0.5), pad_smd(0.7, 0, 0.8, 0.5)], smd=True))
    relay_x = 168
    j_x = 178
    add_fp(fp("RELAY_SRD_5V", f"RELAY{i+5}", "SRD-05VDC-SL-C",
        relay_x, y,
        [pad_tht(-3.81, -2.54, 1.0), pad_tht(-3.81, 2.54, 1.0),
         pad_tht(3.81, -2.54, 1.0), pad_tht(3.81, 2.54, 1.0),
         pad_tht(0, -2.54, 1.0)]))
    add_fp(fp("CONN_7.62_3P", f"J_R{i+5}", "3P 7.62mm",
        j_x, y,
        [pad_tht(-7.62, -2.54, 1.2), pad_tht(0, -2.54, 1.2), pad_tht(7.62, -2.54, 1.2)]))

# ── TEST POINTS ─────────────────────────────────────────────────────────────
tp_y = 0
TP_NAMES = {
    "+12V_PROTECTED": "TP_12V",
    "+5V_SYS": "TP_5V",
    "+3V3_ESP": "TP_3V3ESP",
    "+3V3_ANA": "TP_3V3ANA",
    "GND_STAR": "TP_GND",
    "UART0_TX": "TP_TX",
    "UART0_RX": "TP_RX",
    "EN_ESP": "TP_EN",
    "BOOT_ESP": "TP_BOOT",
    "I2C_SCL": "TP_SCL",
    "I2C_SDA": "TP_SDA",
    "WATCHDOG_KICK": "TP_WD",
    "POWER_GOOD": "TP_PWRGOOD",
    "RELAY_EN": "TP_RLY_EN",
    "BOOT_OK": "TP_BOOT_OK",
    "WATCHDOG_RST": "TP_WD_RST",
}
for net in ["+12V_PROTECTED", "+5V_SYS", "+3V3_ESP", "+3V3_ANA", "GND_STAR",
             "UART0_TX", "UART0_RX", "EN_ESP", "BOOT_ESP",
             "I2C_SCL", "I2C_SDA", "WATCHDOG_KICK",
             "POWER_GOOD", "RELAY_EN", "BOOT_OK", "WATCHDOG_RST"]:
    tp_ref = TP_NAMES.get(net, f"TP_{net[:6]}")
    add_fp(fp("TESTPOINT", tp_ref, net,
        5, tp_y, [pad_smd_circle(0, 0, 1.0)], smd=True))
    tp_y += 3

# ── EXTERNAL CONNECTORS ───────────────────────────────────────────────────
add_fp(fp("CONN_7.62_2P", "J_PWR_EXT", "CONN_7.62_2P",
    190, 20, [pad_tht(-3.81, 0, 1.2), pad_tht(3.81, 0, 1.2)]))

add_fp(fp("CONN_5.08_2x5", "J_EXP_HEADER", "CONN_5.08_2x5",
    90, 42.5,
    [pad_tht(-2.54, 5.08, 0.8), pad_tht(0, 5.08, 0.8), pad_tht(2.54, 5.08, 0.8),
     pad_tht(-2.54, 2.54, 0.8), pad_tht(0, 2.54, 0.8), pad_tht(2.54, 2.54, 0.8),
     pad_tht(-2.54, 0, 0.8), pad_tht(0, 0, 0.8), pad_tht(2.54, 0, 0.8),
     pad_tht(-2.54, -2.54, 0.8), pad_tht(0, -2.54, 0.8), pad_tht(2.54, -2.54, 0.8),
     pad_tht(-2.54, -5.08, 0.8), pad_tht(0, -5.08, 0.8), pad_tht(2.54, -5.08, 0.8)]))

# ESD diodes on expansion GPIO
for i in range(4):
    add_fp(fp("SOT-23", f"D_EXP_ESD{i+1}", "BAT54S",
        75, 40 + i * 4, [
            pad_smd(-0.5, -0.95, 0.6, 0.9), pad_smd(-0.5, 0.95, 0.6, 0.9),
            pad_smd(0.5, 0, 0.6, 0.9),
        ], smd=True))

# ── MOUNTING HOLES ─────────────────────────────────────────────────────────
for mx, my in [(5, 5), (5, 145), (195, 5), (195, 145)]:
    add_fp(fp("M3_HOLE", f"MH_{mx}_{my}", "",
        mx, my, [pad_tht(0, 0, 3.2, 5.0, 5.0)]))

# ═══════════════════════════════════════════════════════════════════════════════
# TRACES — Routes between pads
# Format: (net_name, layer, x1, y1, x2, y2, width)
# Widths: Default=0.25mm, Power=1.0mm, HighVoltage=0.6mm
# ═══════════════════════════════════════════════════════════════════════════════

class Trace:
    def __init__(self, net, layer, x1, y1, x2, y2, width_mm=0.25):
        self.net = net
        self.layer = layer  # "F" or "B"
        self.x1 = x1; self.y1 = y1
        self.x2 = x2; self.y2 = y2
        self.width = width_mm

    def render(self, net_id):
        ux1, uy1, ux2, uy2 = u(self.x1), u(self.y1), u(self.x2), u(self.y2)
        w = u(self.width)
        layer_id = L_FCU if self.layer == "F" else L_BCU
        u_id = uid()
        return (f'  (segment (start {ux1} {uy1}) (end {ux2} {uy2}) '
                f'(width {w}) (layer "{self.layer}.Cu") (net {net_id}) (uuid "{u_id}"))')

class Via:
    def __init__(self, net, x, y, drill=0.4, outer=0.6):
        self.net = net
        self.x = x; self.y = y
        self.drill = drill; self.outer = outer

    def render(self, net_id):
        ux, uy = u(self.x), u(self.y)
        ud = u(self.drill); uo = u(self.outer)
        u_id = uid()
        return (f'  (via (at {ux} {uy}) (size {uo} {uo}) (drill {ud}) '
                f'(layers F.Cu B.Cu) (net {net_id}) (uuid "{u_id}"))')

# Net definitions (code, name)
NETS = [
    (1, "GND_STAR"), (2, "+12V_IN"), (3, "+12V_FUSED"), (4, "+12V_SURGE"),
    (5, "+12V_PROTECTED"), (6, "+5V_MAIN"), (7, "+5V_SYS"), (8, "+5V_RELAY_RAW"),
    (9, "+3V3_MAIN"), (10, "+3V3_ESP"), (11, "+3V3_ANA"),
    (12, "USB_5V"), (13, "USB_5V_RAW"), (14, "USB_5V_FUSED"),
    (15, "SW_5V"), (16, "FB_5V"), (17, "EN_5V"), (18, "BST_5V"),
    (19, "SW_3V3"), (20, "FB_3V3"), (21, "EN_3V3"),
    (22, "NET_SURGE"), (23, "GATE_PROTECT"),
    (24, "UART0_TX"), (25, "UART0_RX"), (26, "I2C_SCL"), (27, "I2C_SDA"),
    (28, "DTR_USB"), (29, "RTS_USB"), (30, "WATCHDOG_KICK"), (31, "WATCHDOG_RST"),
    (32, "EN_ESP"), (33, "BOOT_ESP"), (34, "RELAY1_DRV"), (35, "RELAY2_DRV"),
    (36, "RELAY3_DRV"), (37, "RELAY4_DRV"),
    (38, "DHT22_RAW"), (39, "DS18B20_RAW"),
    (40, "VIN_SENSE_RAW"), (41, "BOOT_OK"),
    (42, "POWER_GOOD"), (43, "RELAY_EN"), (44, "WD_RT"),
    (45, "EXP1_GPIO0"), (46, "EXP1_GPIO1"), (47, "EXP1_GPIO2"), (48, "EXP1_GPIO3"),
    (49, "EXP1_GPIO4"), (50, "EXP1_GPIO5"), (51, "EXP1_GPIO6"), (52, "EXP1_GPIO7"),
    (53, "EXP2_GPIOB0"), (54, "EXP2_GPIOB1"), (55, "EXP2_GPIOB2"), (56, "EXP2_GPIOB3"),
    (57, "NET_RELAY_INTERLOCK"),
    (58, "SD_CS"), (59, "SD_SCK"), (60, "SD_MOSI"), (61, "SD_MISO"),
    (62, "ADS_A0"), (63, "ADS_A1"), (64, "ADS_A2"), (65, "ADS_A3"),
    (66, "NET_VIN_DIV"), (67, "NET_PH_RAW"), (68, "NET_TDS_RAW"),
    (69, "NET_SOIL_SER"), (70, "SOIL_RAW"),
]

NET_MAP = {name: code for code, name in NETS}

TRACES = []
VIAS = []

def t(net, layer, x1, y1, x2, y2, w=0.25):
    TRACES.append(Trace(net, layer, x1, y1, x2, y2, w))

def v(net, x, y, d=0.4, o=0.6):
    VIAS.append(Via(net, x, y, d, o))

# ── POWER TRACES (top layer, heavy copper) ──────────────────────────────────
# +12V_IN → F1 → GDT/MOV → R_SURGE → L_SURGE → Q_PROTECT
t("+12V_IN",    "F", 5, 18, 10, 18, 1.0)
t("+12V_FUSED", "F", 22, 18, 35, 18, 1.0)
t("+12V_SURGE", "F", 48, 18, 62, 18, 1.0)
t("+12V_PROTECTED", "F", 90, 18, 105, 18, 1.0)
t("+12V_PROTECTED", "F", 105, 18, 120, 18, 1.0)  # to caps
t("+12V_PROTECTED", "F", 120, 18, 130, 18, 1.0)  # to buck

# GND star plane connections (via to bottom GND)
for x, y in [(10, 18), (22, 18), (35, 18), (48, 18), (62, 18), (75, 18),
             (90, 18), (105, 18), (120, 18), (130, 18), (10, 25)]:
    t("GND_STAR", "F", x, y, x, y, 0.25)
    v("GND_STAR", x, y)

# +5V_MAIN from L_5V output
t("+5V_MAIN", "F", 83, 35, 93, 35, 1.0)
t("+5V_MAIN", "F", 93, 35, 93, 38, 1.0)
t("+5V_MAIN", "F", 93, 38, 93, 42, 1.0)
t("+5V_MAIN", "F", 93, 42, 100, 42, 1.0)  # feed to next section
t("+5V_MAIN", "F", 100, 42, 100, 35, 1.0)  # feed to buck2
t("+5V_MAIN", "F", 100, 35, 112, 35, 1.0)  # → U3_3V3

# +3V3_MAIN
t("+3V3_MAIN", "F", 123, 35, 133, 35, 0.8)
t("+3V3_MAIN", "F", 133, 35, 133, 42, 0.8)
t("+3V3_MAIN", "F", 133, 42, 133, 38, 0.8)
t("+3V3_MAIN", "F", 133, 38, 133, 34, 0.8)

# Ferrite beads → split rails
t("+3V3_ESP", "F", 58, 47, 63, 47, 0.6)
t("+3V3_ESP", "F", 63, 47, 66, 47, 0.6)
t("+3V3_ANA", "F", 58, 67, 63, 67, 0.6)
t("+3V3_ANA", "F", 63, 67, 66, 67, 0.6)

# OR-ing diodes → +5V_SYS
t("+5V_SYS", "F", 20, 35, 27, 35, 0.6)
t("+5V_SYS", "F", 27, 35, 35, 35, 0.6)
t("+5V_SYS", "F", 35, 35, 40, 35, 0.6)
t("+5V_SYS", "F", 40, 35, 45, 35, 0.6)

# Relay power path
t("+5V_RELAY_RAW", "F", 15, 88, 28, 88, 1.5)
t("+5V_RELAY_RAW", "F", 28, 88, 40, 88, 1.5)
t("+5V_RELAY_RAW", "F", 40, 88, 130, 88, 1.5)  # main relay power rail

# Relay coils 1-4 (Q_R at X=148, RELAY at X=175, D_FLY at X=162)
for i, y in enumerate([93, 110, 127, 144]):
    t("+5V_RELAY_RAW", "F", 130, 88, 130, y, 1.0)
    t("+5V_RELAY_RAW", "F", 130, y, 175, y-2.54, 1.0)  # → RELAY coil+ pad (center X=175, py=-2.54)
    t(f"NET_COIL{i+1}", "F", 148, y, 148, y-2.54, 0.25)  # Q_R collector → coil+
    t(f"RELAY{i+1}_COIL-", "F", 162, y-2.54, 178.81, y-2.54, 0.25)  # D_FLY anode → coil-

# Expansion relay coils 5-8 (Q_R at X=148, RELAY at X=168, D_FLY at X=182)
for i, y in enumerate([93, 110, 127, 144]):
    t("+5V_RELAY_RAW", "F", 175, y-2.54, 182, y-2.54, 1.0)  # extend to D_FLY cathode
    t("+5V_RELAY_RAW", "F", 182, y-2.54, 182, y, 1.0)  # D_FLY cathode via
    t("+5V_RELAY_RAW", "F", 182, y, 168, y-2.54, 1.0)  # → RELAY5 coil+ pad
    t(f"NET_COIL{i+5}", "F", 148, y, 148, y-2.54, 0.25)  # Q_R5-8 collector → coil+
    t(f"RELAY{i+5}_COIL-", "F", 182, y-2.54, 171.81, y-2.54, 0.25)  # D_FLY anode → coil-

# ESP32 +3V3_ESP rail
t("+3V3_ESP", "F", 150, 70, 152, 70, 0.6)
t("+3V3_ESP", "F", 152, 70, 154, 76, 0.6)
t("+3V3_ESP", "F", 165, 75, 165, 70, 0.6)
t("+3V3_ESP", "F", 165, 70, 170, 72, 0.6)  # VIN_SENSE_SER

# +3V3_ANA rail
t("+3V3_ANA", "F", 50, 45, 50, 55, 0.6)
t("+3V3_ANA", "F", 50, 55, 50, 67, 0.6)
t("+3V3_ANA", "F", 50, 67, 82, 57, 0.6)  # U_ADS VDD

# CP2102 +5V_SYS
t("+5V_SYS", "F", 35, 53, 35, 50, 0.6)

# USB power path
t("USB_5V", "F", 25, 30, 32, 30, 0.6)
t("USB_5V_RAW", "F", 32, 30, 39, 30, 0.6)
t("USB_5V_FUSED", "F", 39, 30, 46, 30, 0.6)
t("USB_5V_FUSED", "F", 46, 30, 53, 30, 0.6)

# TPL5010 +3V3_ESP
t("+3V3_ESP", "F", 50, 58, 50, 57, 0.6)

# GND via stitching along relay isolation slot
for x in range(10, 195, 5):
    v("GND_STAR", x, 82)
    v("GND_STAR", x, 86)

# GND stitching everywhere
for x, y in [(72, 35), (72, 38), (72, 32), (112, 35), (112, 38), (112, 32),
             (138, 57), (141, 57), (35, 53), (53, 30)]:
    v("GND_STAR", x, y)

# Via stitching for GND plane (bottom)
for x in range(5, 200, 10):
    for y in range(5, 150, 10):
        v("GND_STAR", x, y)

# ── SIGNAL TRACES ─────────────────────────────────────────────────────────
# USB D+/D- from J_USB → ESD_USB → CP2102
# UART TX/RX: ESP32(165, 52) → (35, 70) → CP2102
t("UART0_TX", "F", 165, 53.8, 160, 53.8, 0.25)
t("UART0_TX", "F", 160, 53.8, 160, 70, 0.25)
t("UART0_TX", "F", 160, 70, 42, 70, 0.25)
t("UART0_TX", "F", 42, 70, 42, 60, 0.25)
t("UART0_TX", "F", 42, 60, 38, 57, 0.25)

t("UART0_RX", "F", 165, 55.9, 158, 55.9, 0.25)
t("UART0_RX", "F", 158, 55.9, 158, 68, 0.25)
t("UART0_RX", "F", 158, 68, 40, 68, 0.25)
t("UART0_RX", "F", 40, 68, 40, 61, 0.25)

# Auto-reset: CP2102 DTR/RTS → Q_RST → EN_ESP
t("DTR_USB", "F", 35, 55, 37, 55, 0.25)
t("DTR_USB", "F", 37, 55, 37, 60, 0.25)

t("RTS_USB", "F", 35, 58, 37, 58, 0.25)
t("RTS_USB", "F", 37, 58, 37, 65, 0.25)

# EN_ESP → TPL5010
t("EN_ESP", "F", 55, 60, 50, 57, 0.25)
v("EN_ESP", 55, 60)

# BOOT_ESP
t("BOOT_ESP", "F", 40, 65, 40, 68, 0.25)

# WATCHDOG_KICK
t("WATCHDOG_KICK", "F", 165, 58.4, 150, 58.4, 0.25)
t("WATCHDOG_KICK", "F", 150, 58.4, 150, 61, 0.25)
t("WATCHDOG_KICK", "F", 150, 61, 47, 61, 0.25)
t("WATCHDOG_KICK", "F", 47, 61, 47, 58, 0.25)

# Watchdog DONE → GPIO4 (ESP32 pin 12)
t("WATCHDOG_RST", "F", 55, 58, 55, 56, 0.25)

# Watchdog R_WD_RT
t("WD_RT", "F", 58, 58, 58, 56, 0.25)
v("WD_RT", 58, 56)

# I2C bus: ESP32 → series → TVS → pull-ups → J_I2C_EXT
# ESP32 SCL (GPIO22) → (156, 62.7) → series → TVS → pull-up → connector
t("I2C_SCL", "F", 165, 62.7, 160, 62.7, 0.25)
t("I2C_SCL", "F", 160, 62.7, 160, 43, 0.25)
t("I2C_SCL", "F", 160, 43, 48, 43, 0.25)
t("I2C_SCL", "F", 48, 43, 43, 43, 0.25)
t("I2C_SCL", "F", 43, 43, 48, 43, 0.25)
t("I2C_SCL", "F", 48, 43, 53, 43, 0.25)
t("I2C_SCL", "F", 53, 43, 60, 43, 0.25)
t("I2C_SCL", "F", 60, 43, 35, 23, 0.25)  # J_I2C_EXT

# I2C SDA
t("I2C_SDA", "F", 165, 60.3, 158, 60.3, 0.25)
t("I2C_SDA", "F", 158, 60.3, 158, 48, 0.25)
t("I2C_SDA", "F", 158, 48, 48, 48, 0.25)
t("I2C_SDA", "F", 48, 48, 43, 48, 0.25)
t("I2C_SDA", "F", 43, 48, 48, 48, 0.25)
t("I2C_SDA", "F", 48, 48, 53, 48, 0.25)
t("I2C_SDA", "F", 53, 48, 60, 48, 0.25)
t("I2C_SDA", "F", 60, 48, 35, 24, 0.25)  # J_I2C_EXT

# ADS1115 I2C (connected to I2C bus)
t("I2C_SCL", "F", 60, 43, 82, 53, 0.25)  # via to ADS
t("I2C_SDA", "F", 60, 48, 82, 51.5, 0.25)

# MCP23017 I2C connections
t("I2C_SCL", "F", 60, 43, 50, 110, 0.25)
t("I2C_SDA", "F", 60, 48, 50, 107.2, 0.25)
t("I2C_SCL", "F", 50, 110, 50, 125, 0.25)
t("I2C_SDA", "F", 50, 125, 50, 122.2, 0.25)

# BME280 / OLED I2C
t("I2C_SCL", "F", 127.5, 55, 127.5, 53.5, 0.25)
t("I2C_SDA", "F", 127.5, 55, 127.5, 56.5, 0.25)
t("I2C_SCL", "F", 127.5, 55, 145, 53.5, 0.25)
t("I2C_SDA", "F", 127.5, 55, 145, 56.5, 0.25)

# Relay drivers
for i, (y, drv) in enumerate([(93, "RELAY1_DRV"), (110, "RELAY2_DRV"), (127, "RELAY3_DRV"), (144, "RELAY4_DRV")]):
    t(drv, "F", 165, 65.2 + i*2.54, 160, 65.2 + i*2.54, 0.25)
    t(drv, "F", 160, 65.2 + i*2.54, 160, y, 0.25)
    t(drv, "F", 160, y, 155, y, 0.25)
    t(drv, "F", 155, y, 148, y, 0.25)  # → Q base

# Expansion relays (via bottom layer to MCP23017)
for i, (y, gpio) in enumerate([(93, "EXP1_GPIO0"), (110, "EXP1_GPIO1"), (127, "EXP1_GPIO2"), (144, "EXP1_GPIO3")]):
    t(gpio, "F", 50, 110 - 2.8 + i*0.7, 40, 110 - 2.8 + i*0.7, 0.25)
    t(gpio, "B", 40, 110 - 2.8 + i*0.7, 40, y, 0.25)
    v(gpio, 40, 110 - 2.8 + i*0.7)
    v(gpio, 40, y)
    t(gpio, "F", 40, y, 130, y, 0.25)
    t(gpio, "F", 130, y, 148, y, 0.25)  # → Q_R5-8 base

# MicroSD SPI
t("SD_CS", "F", 165, 69.8, 160, 69.8, 0.25)
t("SD_CS", "F", 160, 69.8, 160, 74, 0.25)
t("SD_CS", "F", 160, 74, 134, 74, 0.25)
t("SD_CS", "F", 134, 74, 134, 77, 0.25)

t("SD_SCK", "F", 165, 71.1, 160, 71.1, 0.25)
t("SD_SCK", "F", 160, 71.1, 160, 83, 0.25)
t("SD_SCK", "F", 160, 83, 134, 83, 0.25)
t("SD_SCK", "F", 134, 83, 134, 80, 0.25)

t("SD_MOSI", "F", 165, 73.5, 160, 73.5, 0.25)
t("SD_MOSI", "F", 160, 73.5, 160, 80, 0.25)
t("SD_MOSI", "F", 160, 80, 134, 80, 0.25)
t("SD_MOSI", "F", 134, 80, 134, 77, 0.25)

t("SD_MISO", "F", 165, 75.9, 160, 75.9, 0.25)
t("SD_MISO", "F", 160, 75.9, 160, 77, 0.25)
t("SD_MISO", "F", 160, 77, 134, 77, 0.25)
t("SD_MISO", "F", 134, 77, 134, 77, 0.25)

# DHT22 / DS18B20
t("DHT22_RAW", "F", 165, 60.8, 160, 60.8, 0.25)
t("DHT22_RAW", "F", 160, 60.8, 160, 45, 0.25)
t("DHT22_RAW", "F", 160, 45, 48, 45, 0.25)
t("DHT22_RAW", "F", 48, 45, 48, 38, 0.25)
t("DHT22_RAW", "F", 48, 38, 55, 40, 0.25)

t("DS18B20_RAW", "F", 165, 58.4, 160, 58.4, 0.25)
t("DS18B20_RAW", "F", 160, 58.4, 160, 55, 0.25)
t("DS18B20_RAW", "F", 160, 55, 48, 55, 0.25)
t("DS18B20_RAW", "F", 48, 55, 48, 48, 0.25)

# VIN_SENSE
t("VIN_SENSE_RAW", "F", 170, 72, 173, 72, 0.25)
t("VIN_SENSE_RAW", "F", 173, 72, 173, 28, 0.25)
t("VIN_SENSE_RAW", "F", 173, 28, 170, 28, 0.25)

# ADS1115 analog inputs
for i, (x, net) in enumerate([(75, "ADS_A0"), (78, "ADS_A1"), (81, "ADS_A2"), (84, "ADS_A3")]):
    t(net, "F", x, 48, x, 53, 0.25)  # series → ADS
    t(net, "F", x, 53, 82, 51.5 + i, 0.25)  # → ADS pin

# SOIL sensor
t("SOIL_RAW", "F", 35, 55, 32, 55, 0.25)
t("SOIL_RAW", "F", 32, 55, 29, 55, 0.25)
t("SOIL_RAW", "F", 29, 55, 29, 50, 0.25)  # TVS

# Expansion header
for i, (y, net) in enumerate([(47.5, "EXP1_GPIO4"), (45, "EXP1_GPIO5"), (42.5, "EXP1_GPIO6"), (40, "EXP1_GPIO7"),
                                  (37.5, "EXP2_GPIOB0"), (35, "EXP2_GPIOB1"), (32.5, "EXP2_GPIOB2"), (30, "EXP2_GPIOB3")]):
    t(net, "F", 90, y, 75, 40 + i * 4, 0.25)

# POWER_GOOD
t("POWER_GOOD", "F", 138, 57, 138, 60, 0.25)
t("POWER_GOOD", "F", 138, 60, 138, 67, 0.25)

# BOOT_OK
t("BOOT_OK", "F", 165, 53.8, 165, 68, 0.25)
t("BOOT_OK", "F", 165, 68, 166, 68, 0.25)

# RELAY_EN interlock
t("RELAY_EN", "F", 65, 93, 75, 93, 0.25)
t("RELAY_EN", "F", 75, 93, 75, 100, 0.25)
t("RELAY_EN", "F", 75, 100, 148, 100, 0.25)
t("RELAY_EN", "F", 148, 100, 148, 95, 0.25)  # relay driver area

# ═══════════════════════════════════════════════════════════════════════════════
# ZONES (Copper pours)
# ═══════════════════════════════════════════════════════════════════════════════

def gen_zone(net_name, layer, outline, net_id):
    u_id = uid()
    points = " ".join([f"(xy {u(x)} {u(y)})" for x, y in outline])
    return (f'  (zone (net {net_id}) (net_name "{net_name}") '
            f'(layer "{layer}.Cu") (uuid "{u_id}")\n'
            f'    (hatch edge 0.5)\n'
            f'    (connect_pads (clearance 0.2))\n'
            f'    (min_thickness 0.15)\n'
            f'    (fill (yes) (thermal_gap 0.2) (thermal_bridge_width 0.3))\n'
            f'    (polygon\n'
            f'      (pts\n'
            f'        {points}\n'
            f'      )\n'
            f'    )\n'
            f'  )')

# BOTTOM layer GND plane (full board minus relay zone keepout and antenna zone)
gnd_zone_bcu = gen_zone("GND_STAR", "B", [
    (1.0, 1.0), (199.0, 1.0), (199.0, 149.0), (1.0, 149.0)
], 1)

# TOP layer GND pour (floating islands, not full plane)
gnd_zone_fcu = gen_zone("GND_STAR", "F", [
    (5.0, 5.0), (105.0, 5.0), (105.0, 80.0), (5.0, 80.0)
], 1)

# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE PCB FILE
# ═══════════════════════════════════════════════════════════════════════════════

def gen_pcb():
    lines = [
        f'(kicad_pcb (version 20230108) (generator "EcoSynTech_PCB_v6.3")',
        f'  (general',
        f'    (thickness {THICKNESS})',
        f'    (drawings 0)',
        f'    (tracks {len(TRACES)})',
        f'    (zones 2)',
        f'    (modules {len(FP_LIST)})',
        f'    (nets {len(NETS)})',
        f'  )',
        f'  (page "A3")',
        f'  (title_block',
        f'    (title "EcoSynTech PCB v6.3")',
        f'    (company "EcoSynTech Global")',
        f'    (rev "6.3 Final")',
        f'    (date "2026-04-16")',
        f'    (source "EcoSynTech_V6_3_Final")',
        f'  )',
        f'  (layers',
        f'    (0 "F.Cu" signal)',
        f'    (31 "B.Cu" signal)',
        f'    (32 "B.Adhes" user)',
        f'    (33 "F.Adhes" user)',
        f'    (34 "B.Paste" user)',
        f'    (35 "F.Paste" user)',
        f'    (36 "B.SilkS" user)',
        f'    (37 "F.SilkS" user)',
        f'    (38 "B.Mask" user)',
        f'    (39 "F.Mask" user)',
        f'    (40 "Dwgs.User" user)',
        f'    (41 "Cmts.User" user)',
        f'    (42 "Eco1.User" user)',
        f'    (43 "Eco2.User" user)',
        f'    (44 "Edge.Cuts" user)',
        f'    (45 "Margin" user)',
        f'    (46 "B.CrtYd" user)',
        f'    (47 "F.CrtYd" user)',
        f'  )',
    ]

    # Setup
    lines.extend([
        f'  (setup',
        f'    (stackup',
        f'      (copper_finish "ENIG")',
        f'      (dielectric_constraints yes)',
        f'    )',
        f'    (pad_to_mask_clearance 0.05)',
        f'    (solder_mask_min_width 0.0)',
        f'    (pcbplotparams',
        f'      (layerselection 0x00010f8000001801)',
        f'      (plot_on_all_layers_selection 0x0000000000000000)',
        f'      (disableapertmacros no)',
        f'      (usegerberextensions no)',
        f'      (usegerberattributes no)',
        f'      (usegerberadvancedattributes no)',
        f'      (creategerberjobfile no)',
        f'      (svgformat no)',
        f'      (drilldefinitiontype metric)',
        f'      (metricaccuracy yes)',
        f'      (widthselection 0)',
        f'      (heightselection 0)',
        f'      (maxdrlerror 0)',
        f'      (minwidth 0.15)',
        f'      (dimdrill 0.0)',
        f'      (dimdsrc 0.0)',
        f'      (dimsdrd 0.0)',
        f'      (drdsigma 0)',
        f'      (textpresentation)',
        f'      (mirror)',
        f'      (plotformat pdf)',
        f'      (layerselectionpads)',
        f'      (currentplotformat)',
        f'      (outputdirectory "")',
        f'    )',
        f'    (pad_drill_size_pair 0.4 0.4)',
        f'    (pad_drill_size_min 0.4)',
        f'    (pad_drill_size_max 0.4)',
        f'    (via_drill_size_pair 0.4 0.4)',
        f'    (via_drill_size_min 0.25)',
        f'    (via_drill_size_max 0.4)',
        f'    (default_via 0 0.4 0.6)',
        f'    (default_viad 0.4 0.6)',
        f'    (blindburried_via 0 0.4 0.6)',
        f'    (viastackinclusions)',
        f'    (track_duct 0 0 1)',
        f'    (graphics_coordinate_system -0.5 0.5 0 0 1 0 0)',
        f'    (text_coordinate_system 0 0 0.3 0)',
        f'    (default_text_size 1.27)',
        f'    (default_text_thickness 0.15)',
        f'    (grid_requirements (size 1.27mm))',
        f'  )',
    ])

    # Net classes
    lines.extend([
        f'  (net_classes',
        f'    (default',
        f'      (name "Default")',
        f'      (clearance 0.2)',
        f'      (track_width 0.25)',
        f'      (via_dia 0.6)',
        f'      (via_drill 0.4)',
        f'      (uvia_dia 0.4)',
        f'      (uvia_drill 0.4)',
        f'    )',
        f'    (class "Power"',
        f'      (name "Power")',
        f'      (clearance 0.4)',
        f'      (track_width 1.0)',
         f'      (via_dia 0.8)',
         f'      (via_drill 0.4)',
         f'      (uvia_dia 0.4)',
         f'      (uvia_drill 0.4)',
         f'    )',
         f'    (class "HighVoltage"',
        f'      (name "HighVoltage")',
        f'      (clearance 0.4)',
        f'      (track_width 0.6)',
        f'      (via_dia 0.6)',
        f'      (via_drill 0.4)',
        f'      (uvia_dia 0.4)',
        f'      (uvia_drill 0.4)',
        f'    )',
        f'  )',
    ])

    # Net definitions
    for code, name in NETS:
        lines.append(f'  (net (code {code}) (name "{name}"))')
    lines.append('')

    # Footprints
    for fp_obj in FP_LIST:
        lines.append(fp_obj.render())
    lines.append('')

    # Traces
    for trace in TRACES:
        net_id = NET_MAP.get(trace.net, 1)
        lines.append(trace.render(net_id))
    lines.append('')

    # Vias
    for via in VIAS:
        net_id = NET_MAP.get(via.net, 1)
        lines.append(via.render(net_id))
    lines.append('')

    # Copper zones
    lines.append(gnd_zone_bcu)
    lines.append(gnd_zone_fcu)
    lines.append('')

    # Board outline (Edge.Cuts) with 45-degree chamfer
    chamfer = u(3.0)
    edges = [
        (0, BOARD_H, chamfer, BOARD_H),
        (chamfer, BOARD_H, BOARD_W-chamfer, BOARD_H),
        (BOARD_W-chamfer, BOARD_H, BOARD_W, BOARD_H-chamfer),
        (BOARD_W, BOARD_H-chamfer, BOARD_W, chamfer),
        (BOARD_W, chamfer, BOARD_W-chamfer, 0),
        (BOARD_W-chamfer, 0, chamfer, 0),
        (chamfer, 0, 0, chamfer),
        (0, chamfer, 0, BOARD_H-chamfer),
    ]
    for sx, sy, ex, ey in edges:
        lines.append(f'  (gr_line (start {sx} {sy}) (end {ex} {ey}) '
                    f'(layer Edge.Cuts) (width {u(0.1)}) (tstamp "{uid()}"))')

    # Relay isolation slot (cutout between relay and logic zones)
    slot_uuid = uid()
    lines.append(f'  (gr_line (start {u(1)} {u(82)}) (end {u(199)} {u(82)}) '
                f'(layer Edge.Cuts) (width {u(0.3)}) (tstamp "{slot_uuid}"))')
    lines.append(f'  (gr_line (start {u(1)} {u(86)}) (end {u(199)} {u(86)}) '
                f'(layer Edge.Cuts) (width {u(0.3)}) (tstamp "{uid()}"))')

    # Silkscreen elements
    def gr_text(text, x, y, sz=1.5, th=0.2):
        lines.append(f'  (gr_text "{text}" (at {u(x)} {u(y)} 0) '
                    f'(layer F.SilkS) (tstamp "{uid()}")')
        lines.append(f'    (effects (font (size {sz} {sz}) (thickness {th})))')
        lines.append('  )')

    gr_text("EcoSynTech V6.3 Industrial Pro", 100, 148, 2.0, 0.3)
    gr_text("Rev 6.3 Final | 2-Layer | ENIG | FR-4 Tg130", 100, 145, 1.5, 0.2)
    gr_text("CAUTION: HIGH VOLTAGE 220VAC", 100, 95, 1.8, 0.25)
    gr_text("THAY DUNG GIA TRI CAU CHI", 100, 92, 1.5, 0.2)
    gr_text("KIEM TRA CUC TINH TRUOC KHI CAP NGUON", 100, 89, 1.5, 0.2)
    gr_text("ANTENNA KEEPOUT ZONE", 165, 75, 1.2, 0.15)
    gr_text("DO NOT REMOVE SNUBBER - ARC HAZARD", 100, 97, 1.2, 0.15)
    gr_text("EcoSynTech Global | ecosyntech68vn", 100, 2, 1.0, 0.1)
    gr_text("2026-04-16", 195, 2, 1.0, 0.1)

    lines.append(')')
    return '\n'.join(lines)

if __name__ == "__main__":
    print("=== EcoSynTech PCB v6.3 — PCB Generator ===")
    print(f"  Footprints: {len(FP_LIST)}")
    print(f"  Traces: {len(TRACES)}")
    print(f"  Vias: {len(VIAS)}")

    pcb = gen_pcb()
    path = f"{OUT}/{PROJ}.kicad_pcb"
    with open(path, "w") as f:
        f.write(pcb)
    print(f"  PCB: {path} ({len(pcb)} bytes)")
    print("Done!")
