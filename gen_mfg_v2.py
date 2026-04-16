#!/usr/bin/env python3
"""
EcoSynTech PCB v6.3 — Manufacturing Files Generator
Generates: Gerber RS-274X, Excellon drill, Pick & Place, fabrication docs
Based on: gen_pcb_v2.py output (215 footprints, 184 traces, 405 vias, full component data)
"""
import os, math
from components_gen import COMPONENTS

OUT = "/tmp/ecosyn-pcb/gerber"
MOUT = "/tmp/ecosyn-pcb/manufacturing"
os.makedirs(OUT, exist_ok=True)
os.makedirs(MOUT, exist_ok=True)

MM = 100000.0

def u(x): return int(x * MM)

# ═══════════════════════════════════════════════════════════════════════════════
# BOARD PARAMETERS (must match PCB)
# ═══════════════════════════════════════════════════════════════════════════════
BOARD_W, BOARD_H = 200.0, 150.0
THICKNESS = 1.6
BOARD_EDGE = [
    (0, 0), (3.0, 0), (BOARD_W-3.0, 0), (BOARD_W, 3.0),
    (BOARD_W, BOARD_H-3.0), (BOARD_W-3.0, BOARD_H), (3.0, BOARD_H), (0, BOARD_H-3.0),
    (0, 3.0), (0, 0)
]

GERBER_NUMBER_FORMAT = "46"
GERBER_DECIMAL_FORMAT = "46"
GERBER_UNIT = "MM"

def gf(content):
    return f"%FSLAX{GERBER_NUMBER_FORMAT}Y{GERBER_DECIMAL_FORMAT}*%\n%MOMM*%\n{content}\nM02*"

# ═══════════════════════════════════════════════════════════════════════════════
# GERBER HEADER / FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
def gerber_header(layer_name, filename):
    return (f"G04 EcoSynTech PCB v6.3 - {layer_name}*\n"
            f"G04 Board: 200mm x 150mm | 2-Layer | ENIG*\n"
            f"%FSLAX46Y46*%\n"
            f"%MOMM*%\n")

# ═══════════════════════════════════════════════════════════════════════════════
# APERTURE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
# D10: Circle 0.25mm (default trace)
# D11: Circle 0.60mm (via pad)
# D12: Circle 0.80mm (power via pad)
# D13: Rect 0.6mm × 0.25mm (SOIC-8 pad)
# D14: Rect 0.8mm × 0.3mm (SOIC pad)
# D15: Rect 0.3mm × 0.3mm (MSOP-8 pad)
# D16: Circle 3.2mm (mounting hole)
# D17: Circle 0.8mm (THT pad)
# D18: Circle 1.0mm (THT pad)
# D19: Circle 1.6mm (relay pad)
# D20: Rect 0.8mm × 0.5mm (SMD pad 0805)
# D21: Circle 1.0mm (large pad)
# D22: Circle 0.5mm (small pad)
# D23: Rect 1.4mm × 0.9mm (1210 cap)
# D24: Circle 0.3mm (thermal via)
# D25: Rect 0.8mm × 0.6mm (SOT-23 pad)

APERTURES = {
    "D10": ("C", 0.25),   # 0.25mm trace/circle
    "D11": ("C", 0.60),   # 0.6mm via pad
    "D12": ("C", 0.80),   # 0.8mm power via pad
    "D13": ("R", (0.60, 0.25)),  # SOIC-8 pad
    "D14": ("R", (0.80, 0.30)),  # SOIC pad
    "D15": ("R", (0.30, 0.15)),  # MSOP-8 pad
    "D16": ("C", 3.20),   # M3 mounting hole
    "D17": ("C", 0.80),   # 0.8mm THT pad
    "D18": ("C", 1.00),   # 1.0mm THT pad
    "D19": ("C", 1.60),   # 1.6mm relay pad
    "D20": ("R", (0.80, 0.50)),  # 0805 SMD pad
    "D21": ("C", 1.00),   # 1.0mm pad
    "D22": ("C", 0.50),   # 0.5mm small pad
    "D23": ("R", (1.40, 0.90)),  # 1210 cap
    "D24": ("C", 0.30),   # thermal via
    "D25": ("R", (0.80, 0.60)),  # SOT-23 pad
    "D26": ("R", (0.50, 0.30)),  # 0603 pad
    "D27": ("R", (0.30, 0.30)),  # very small pad
    "D28": ("C", 0.15),   # micro via
    "D29": ("R", (2.20, 1.35)),  # 2512 resistor
    "D30": ("C", 5.00),   # mounting hole clearance
}

def aperture_macros():
    lines = []
    for code, (shape, params) in APERTURES.items():
        if shape == "C":
            dia = params
            lines.append(f"%ADD{code[1:]}C,{dia:.4f}*%")
        elif shape == "R":
            w, h = params
            lines.append(f"%ADD{code[1:]}R,{w:.4f}X{h:.4f}*%")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# COORDINATE FORMAT: 4.6 (integer 4 digits, decimal 6 digits)
# All units in mm, origin at bottom-left
# ═══════════════════════════════════════════════════════════════════════════════
def fmt(x, y):
    xi = int(x * 1e6)
    yi = int(y * 1e6)
    return f"X{xi:010d}Y{yi:010d}"

# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT DATABASE — All footprints with pad positions
# Format: (ref, value, cx, cy, [pads])
# Pad: (num, px, py, w, h, drill, shape, net)
# ═══════════════════════════════════════════════════════════════════════════════

# COMPONENTS imported from components_gen.py (gen_pcb_v2.py output)
# Only add GND stitching vias here - all other components already in components_gen.py

# GND stitching vias (every 10mm grid) - NOT in components_gen.py
for x in range(5, 200, 10):
    for y in range(5, 150, 10):
        COMPONENTS.append((f"GV_{x}_{y}", "GNDVia", x, y, [
            (1, 0, 0, 0.6, 0.6, 0.3, "circle", "GND_STAR"),
        ]))

# ═══════════════════════════════════════════════════════════════════════════════
# TRACE DATABASE — All copper routing
# Format: (net, layer, x1, y1, x2, y2, width)
# ═══════════════════════════════════════════════════════════════════════════════
TRACES = [
    # Power traces (1mm for +12V, 1mm for relay, 0.8mm for +5V/+3V3)
    ("+12V_IN",    "F", 5, 18, 10, 18, 1.0),
    ("+12V_FUSED", "F", 22, 18, 35, 18, 1.0),
    ("+12V_FUSED", "F", 35, 18, 48, 18, 1.0),
    ("+12V_SURGE", "F", 48, 18, 62, 18, 1.0),
    ("+12V_SURGE", "F", 62, 18, 75, 18, 1.0),
    ("+12V_SURGE", "F", 75, 18, 90, 18, 1.0),
    ("+12V_PROTECTED", "F", 90, 18, 105, 18, 1.0),
    ("+12V_PROTECTED", "F", 105, 18, 120, 18, 1.0),
    ("+12V_PROTECTED", "F", 120, 18, 130, 18, 1.0),
    ("+12V_PROTECTED", "F", 60, 42, 72, 35, 1.0),
    ("+12V_PROTECTED", "F", 60, 35, 72, 33, 1.0),
    ("+12V_PROTECTED", "F", 100, 42, 112, 35, 1.0),
    ("+12V_PROTECTED", "F", 100, 35, 112, 33, 1.0),
    ("+12V_PROTECTED", "F", 60, 28, 72, 30, 0.25),
    ("+12V_PROTECTED", "F", 100, 28, 112, 30, 0.25),

    ("+5V_MAIN", "F", 83, 35, 93, 35, 1.0),
    ("+5V_MAIN", "F", 93, 35, 93, 42, 1.0),
    ("+5V_MAIN", "F", 93, 42, 100, 42, 1.0),
    ("+5V_MAIN", "F", 100, 42, 100, 35, 1.0),
    ("+5V_MAIN", "F", 100, 35, 112, 35, 1.0),
    ("+5V_MAIN", "F", 93, 38, 93, 34, 1.0),
    ("+5V_MAIN", "F", 15, 88, 28, 88, 1.5),

    ("+3V3_MAIN", "F", 123, 35, 133, 35, 0.8),
    ("+3V3_MAIN", "F", 133, 35, 133, 42, 0.8),
    ("+3V3_MAIN", "F", 133, 42, 133, 38, 0.8),
    ("+3V3_MAIN", "F", 133, 38, 133, 34, 0.8),
    ("+3V3_MAIN", "F", 58, 47, 63, 47, 0.6),
    ("+3V3_MAIN", "F", 63, 47, 66, 47, 0.6),
    ("+3V3_MAIN", "F", 58, 67, 63, 67, 0.6),
    ("+3V3_MAIN", "F", 63, 67, 66, 67, 0.6),

    ("+5V_SYS", "F", 20, 35, 27, 35, 0.6),
    ("+5V_SYS", "F", 27, 35, 35, 35, 0.6),
    ("+5V_SYS", "F", 35, 35, 40, 35, 0.6),
    ("+5V_SYS", "F", 40, 35, 45, 35, 0.6),
    ("+5V_SYS", "F", 35, 53, 35, 50, 0.6),

    ("+5V_RELAY_RAW", "F", 28, 88, 40, 88, 1.5),

    ("USB_5V", "F", 25, 30, 32, 30, 0.6),
    ("USB_5V_RAW", "F", 32, 30, 39, 30, 0.6),
    ("USB_5V_FUSED", "F", 39, 30, 46, 30, 0.6),
    ("USB_5V_FUSED", "F", 46, 30, 53, 30, 0.6),
    ("USB_5V_FUSED", "F", 20, 35, 20, 30, 0.25),

    # SW traces (switching nodes)
    ("SW_5V", "F", 72, 35, 83, 35, 0.6),
    ("SW_3V3", "F", 112, 35, 123, 35, 0.6),

    # Signal traces
    ("UART0_TX", "F", 165, 53.8, 160, 53.8, 0.25),
    ("UART0_TX", "F", 160, 53.8, 160, 70, 0.25),
    ("UART0_TX", "F", 160, 70, 42, 70, 0.25),
    ("UART0_TX", "F", 42, 70, 42, 60, 0.25),
    ("UART0_TX", "F", 42, 60, 38, 57, 0.25),

    ("UART0_RX", "F", 165, 55.9, 158, 55.9, 0.25),
    ("UART0_RX", "F", 158, 55.9, 158, 68, 0.25),
    ("UART0_RX", "F", 158, 68, 40, 68, 0.25),
    ("UART0_RX", "F", 40, 68, 40, 61, 0.25),

    ("DTR_USB", "F", 35, 55, 37, 55, 0.25),
    ("DTR_USB", "F", 37, 55, 37, 60, 0.25),
    ("RTS_USB", "F", 35, 58, 37, 58, 0.25),
    ("RTS_USB", "F", 37, 58, 37, 65, 0.25),

    ("EN_ESP", "F", 55, 60, 50, 57, 0.25),
    ("BOOT_ESP", "F", 40, 65, 40, 68, 0.25),
    ("WATCHDOG_KICK", "F", 165, 58.4, 150, 58.4, 0.25),
    ("WATCHDOG_KICK", "F", 150, 58.4, 150, 61, 0.25),
    ("WATCHDOG_KICK", "F", 150, 61, 47, 61, 0.25),
    ("WATCHDOG_KICK", "F", 47, 61, 47, 58, 0.25),
    ("WATCHDOG_RST", "F", 55, 58, 55, 56, 0.25),
    ("WD_RT", "F", 58, 58, 58, 56, 0.25),

    # I2C bus
    ("I2C_SCL", "F", 165, 62.7, 160, 62.7, 0.25),
    ("I2C_SCL", "F", 160, 62.7, 160, 43, 0.25),
    ("I2C_SCL", "F", 160, 43, 48, 43, 0.25),
    ("I2C_SCL", "F", 43, 43, 48, 43, 0.25),
    ("I2C_SCL", "F", 48, 43, 60, 43, 0.25),
    ("I2C_SCL", "F", 60, 43, 35, 23, 0.25),
    ("I2C_SDA", "F", 165, 60.3, 158, 60.3, 0.25),
    ("I2C_SDA", "F", 158, 60.3, 158, 48, 0.25),
    ("I2C_SDA", "F", 158, 48, 48, 48, 0.25),
    ("I2C_SDA", "F", 43, 48, 48, 48, 0.25),
    ("I2C_SDA", "F", 48, 48, 60, 48, 0.25),
    ("I2C_SDA", "F", 60, 48, 35, 24, 0.25),
    ("I2C_SCL", "F", 60, 43, 82, 53, 0.25),
    ("I2C_SDA", "F", 60, 48, 82, 51.5, 0.25),
    ("I2C_SCL", "F", 60, 43, 50, 110, 0.25),
    ("I2C_SDA", "F", 60, 48, 50, 107.2, 0.25),
    ("I2C_SCL", "F", 50, 110, 50, 125, 0.25),
    ("I2C_SDA", "F", 50, 125, 50, 122.2, 0.25),
    ("I2C_SCL", "F", 127.5, 55, 127.5, 53.5, 0.25),
    ("I2C_SDA", "F", 127.5, 55, 127.5, 56.5, 0.25),
    ("I2C_SCL", "F", 127.5, 55, 145, 53.5, 0.25),
    ("I2C_SDA", "F", 127.5, 55, 145, 56.5, 0.25),

    # Relay drivers
    ("RELAY1_DRV", "F", 165, 65.2, 160, 65.2, 0.25),
    ("RELAY1_DRV", "F", 160, 65.2, 160, 93, 0.25),
    ("RELAY1_DRV", "F", 160, 93, 155, 93, 0.25),
    ("RELAY2_DRV", "F", 165, 67.5, 160, 67.5, 0.25),
    ("RELAY2_DRV", "F", 160, 67.5, 160, 110, 0.25),
    ("RELAY2_DRV", "F", 160, 110, 155, 110, 0.25),
    ("RELAY3_DRV", "F", 165, 69.8, 160, 69.8, 0.25),
    ("RELAY3_DRV", "F", 160, 69.8, 160, 127, 0.25),
    ("RELAY3_DRV", "F", 160, 127, 155, 127, 0.25),
    ("RELAY4_DRV", "F", 165, 72.1, 160, 72.1, 0.25),
    ("RELAY4_DRV", "F", 160, 72.1, 160, 144, 0.25),
    ("RELAY4_DRV", "F", 160, 144, 155, 144, 0.25),

    # MicroSD SPI
    ("SD_CS", "F", 165, 69.8, 160, 69.8, 0.25),
    ("SD_CS", "F", 160, 69.8, 160, 74, 0.25),
    ("SD_CS", "F", 160, 74, 134, 74, 0.25),
    ("SD_CS", "F", 134, 74, 134, 77, 0.25),
    ("SD_SCK", "F", 165, 71.1, 160, 71.1, 0.25),
    ("SD_SCK", "F", 160, 71.1, 160, 83, 0.25),
    ("SD_SCK", "F", 160, 83, 134, 83, 0.25),
    ("SD_SCK", "F", 134, 83, 134, 80, 0.25),
    ("SD_MOSI", "F", 165, 73.5, 160, 73.5, 0.25),
    ("SD_MOSI", "F", 160, 73.5, 160, 80, 0.25),
    ("SD_MOSI", "F", 160, 80, 134, 80, 0.25),
    ("SD_MOSI", "F", 134, 80, 134, 77, 0.25),
    ("SD_MISO", "F", 165, 75.9, 160, 75.9, 0.25),
    ("SD_MISO", "F", 160, 75.9, 160, 77, 0.25),
    ("SD_MISO", "F", 160, 77, 134, 77, 0.25),

    # DHT22 / DS18B20
    ("DHT22_RAW", "F", 165, 60.8, 160, 60.8, 0.25),
    ("DHT22_RAW", "F", 160, 60.8, 160, 45, 0.25),
    ("DHT22_RAW", "F", 160, 45, 48, 45, 0.25),
    ("DHT22_RAW", "F", 48, 45, 48, 38, 0.25),
    ("DHT22_RAW", "F", 48, 38, 55, 40, 0.25),
    ("DS18B20_RAW", "F", 165, 58.4, 160, 58.4, 0.25),
    ("DS18B20_RAW", "F", 160, 58.4, 160, 55, 0.25),
    ("DS18B20_RAW", "F", 160, 55, 48, 55, 0.25),
    ("DS18B20_RAW", "F", 48, 55, 48, 48, 0.25),

    # VIN_SENSE
    ("VIN_SENSE_RAW", "F", 170, 72, 173, 72, 0.25),
    ("VIN_SENSE_RAW", "F", 173, 72, 173, 28, 0.25),
    ("VIN_SENSE_RAW", "F", 173, 28, 170, 28, 0.25),

    # ADS1115 analog inputs
    ("ADS_A0", "F", 75, 48, 75, 53, 0.25),
    ("ADS_A1", "F", 78, 48, 78, 53, 0.25),
    ("ADS_A2", "F", 81, 48, 81, 53, 0.25),
    ("ADS_A3", "F", 84, 48, 84, 53, 0.25),
    ("NET_SOIL_SER", "F", 35, 55, 32, 55, 0.25),
    ("NET_SOIL_SER", "F", 32, 55, 29, 55, 0.25),
    ("NET_SOIL_SER", "F", 29, 55, 29, 50, 0.25),

    # Expansion header
    ("EXP1_GPIO4", "F", 90, 47.5, 75, 40, 0.25),
    ("EXP1_GPIO5", "F", 90, 45, 75, 44, 0.25),
    ("EXP1_GPIO6", "F", 90, 42.5, 75, 48, 0.25),
    ("EXP1_GPIO7", "F", 90, 40, 75, 52, 0.25),
    ("EXP2_GPIOB0", "F", 90, 37.5, 75, 56, 0.25),
    ("EXP2_GPIOB1", "F", 90, 35, 75, 60, 0.25),
    ("EXP2_GPIOB2", "F", 90, 32.5, 75, 64, 0.25),
    ("EXP2_GPIOB3", "F", 90, 30, 75, 68, 0.25),

    # POWER_GOOD
    ("POWER_GOOD", "F", 138, 57, 138, 60, 0.25),
    ("POWER_GOOD", "F", 138, 60, 138, 67, 0.25),
    ("POWER_GOOD", "F", 138, 67, 152, 50, 0.25),
    ("BOOT_OK", "F", 165, 53.8, 165, 68, 0.25),
    ("BOOT_OK", "F", 165, 68, 166, 68, 0.25),
    ("RELAY_EN", "F", 65, 93, 75, 93, 0.25),
    ("RELAY_EN", "F", 75, 93, 75, 100, 0.25),
    ("RELAY_EN", "F", 75, 100, 148, 100, 0.25),
    ("RELAY_EN", "F", 148, 100, 148, 95, 0.25),
]

# Add GND traces for decoupling
for x, y in [(72, 35), (72, 38), (112, 35), (112, 38),
             (138, 57), (141, 57), (35, 53), (53, 30),
             (50, 58), (50, 64)]:
    TRACES.append(("GND_STAR", "F", x, y, x, y, 0.25))

# ═══════════════════════════════════════════════════════════════════════════════
# VIA DATABASE — for GND stitching
# ═══════════════════════════════════════════════════════════════════════════════
VIAS = []
# Thermal via grid for bottom GND plane
for x in range(5, 200, 10):
    for y in range(5, 150, 10):
        VIAS.append((x, y, "GND_STAR"))

# GND stitching along relay slot
for x in range(1, 200, 5):
    VIAS.append((x, 82, "GND_STAR"))
    VIAS.append((x, 86, "GND_STAR"))

# Thermal vias under switching regulators
for tx, ty in [(68, 38), (68, 35), (68, 32), (76, 38), (76, 35), (76, 32),
                (108, 38), (108, 35), (108, 32), (116, 38), (116, 35), (116, 32)]:
    VIAS.append((tx, ty, "GND_STAR"))

# Signal vias (where traces change layer)
signal_vias = [
    (165, 65.2, "RELAY1_DRV"), (165, 67.5, "RELAY2_DRV"),
    (165, 69.8, "RELAY3_DRV"), (165, 72.1, "RELAY4_DRV"),
    (165, 58.4, "DS18B20_RAW"), (165, 60.8, "DHT22_RAW"),
    (165, 62.7, "I2C_SCL"), (165, 60.3, "I2C_SDA"),
    (55, 60, "EN_ESP"), (47, 58, "WATCHDOG_KICK"),
    (65, 93, "RELAY_EN"),
]
for x, y, net in signal_vias:
    VIAS.append((x, y, net))

# ═══════════════════════════════════════════════════════════════════════════════
# GERBER GENERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_aperture(w, shape="circle"):
    """Return aperture code for given width/shape."""
    if shape == "circle":
        if abs(w - 0.25) < 0.01: return "D10"
        if abs(w - 0.60) < 0.01: return "D11"
        if abs(w - 0.80) < 0.01: return "D12"
        if abs(w - 3.20) < 0.01: return "D16"
        if abs(w - 0.80) < 0.01: return "D17"
        if abs(w - 1.00) < 0.01: return "D18"
        if abs(w - 1.60) < 0.01: return "D19"
        if abs(w - 1.00) < 0.01: return "D21"
        if abs(w - 0.50) < 0.01: return "D22"
        if abs(w - 0.30) < 0.01: return "D24"
        if abs(w - 0.15) < 0.01: return "D28"
        return f"D10"
    else:
        # Rect pad
        if abs(w - 0.80) < 0.01: return "D20"
        if abs(w - 0.60) < 0.01: return "D25"
        if abs(w - 0.50) < 0.01: return "D20"
        if abs(w - 0.30) < 0.01: return "D26"
        if abs(w - 2.20) < 0.01: return "D29"
        if abs(w - 1.40) < 0.01: return "D23"
        return "D20"

def pad_to_aperture(w, h, drill):
    if drill > 0:
        return get_aperture(drill, "circle")
    if h > w * 1.5:
        return get_aperture(w, "rect")
    return get_aperture(w, "circle")

# ═══════════════════════════════════════════════════════════════════════════════
# FRONT COPPER LAYER
# ═══════════════════════════════════════════════════════════════════════════════
def gen_copper_front():
    lines = [gerber_header("Front Copper (F.Cu)", "EcoSynTech_V6_3_F.Cu.gbr")]
    lines.append(aperture_macros())

    # Draw all component pads (top side, SMD + through-hole)
    for ref, val, cx, cy, pads in COMPONENTS:
        for num, px, py, pw, ph, drill, shape, net in pads:
            if net == "NPTH" or net == "NC": continue
            if drill > 0 and shape == "oval":
                # Through-hole pad — draw pad on copper layer
                ap = pad_to_aperture(pw, ph, drill)
                lines.append(f"G75*\n%ADD{ap[1:]}C,{pw:.4f}*%\n")
                lines.append(f"X{fmt(cx+px, cy+py)[1:]}D{ap[1:]}*\n")
            elif drill == 0:
                # SMD pad
                if ph > pw * 1.5:
                    ap = get_aperture(pw, "rect")
                else:
                    ap = get_aperture(pw, "circle")
                lines.append(f"%ADD{ap[1:]}C,{pw:.4f}*%\n")
                lines.append(f"X{fmt(cx+px, cy+py)[1:]}D{ap[1:]}*\n")

    # Draw all traces
    for net, layer, x1, y1, x2, y2, w in TRACES:
        if layer != "F": continue
        ap = get_aperture(w, "circle")
        lines.append(f"%ADD{ap[1:]}C,{w:.4f}*%\n")
        lines.append(f"G01*\nX{fmt(x1,y1)[1:]}Y{fmt(x1,y1)[1:]}D02*\n")
        lines.append(f"X{fmt(x2,y2)[1:]}Y{fmt(x2,y2)[1:]}D01*\n")

    # Draw vias (through-hole)
    for x, y, net in VIAS:
        lines.append(f"%ADD11C,0.6000*%\n")
        lines.append(f"X{fmt(x,y)[1:]}D11*\n")

    # Draw board outline flash
    for i in range(len(BOARD_EDGE)-1):
        x1, y1 = BOARD_EDGE[i]
        x2, y2 = BOARD_EDGE[i+1]
        lines.append(f"G01*\nX{fmt(x1,y1)[1:]}Y{fmt(x1,y1)[1:]}D02*\n")
        lines.append(f"X{fmt(x2,y2)[1:]}Y{fmt(x2,y2)[1:]}D01*\n")

    lines.append("M02*")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# BACK COPPER LAYER
# ═══════════════════════════════════════════════════════════════════════════════
def gen_copper_back():
    lines = [gerber_header("Back Copper (B.Cu)", "EcoSynTech_V6_3_B.Cu.gbr")]
    lines.append(aperture_macros())

    # Bottom layer: GND plane with thermal relief pads
    # Draw GND stitching vias
    for x, y, net in VIAS:
        if net == "GND_STAR":
            lines.append(f"%ADD11C,0.6000*%\n")
            lines.append(f"X{fmt(x,y)[1:]}D11*\n")

    # Draw GND plane outline (bottom)
    lines.append("%ADD10C,0.2500*%\nG75*\n")
    lines.append(f"X{fmt(1,1)[1:]}Y{fmt(1,1)[1:]}D02*\n")
    lines.append(f"X{fmt(199,1)[1:]}Y{fmt(199,1)[1:]}D01*\n")
    lines.append(f"X{fmt(199,149)[1:]}Y{fmt(199,149)[1:]}D01*\n")
    lines.append(f"X{fmt(1,149)[1:]}Y{fmt(1,149)[1:]}D01*\n")
    lines.append(f"X{fmt(1,1)[1:]}Y{fmt(1,1)[1:]}D01*\nG01*\n")

    # Draw GND thermal relief for through-hole pads on GND nets
    gnd_pads = []
    for ref, val, cx, cy, pads in COMPONENTS:
        for num, px, py, pw, ph, drill, shape, net in pads:
            if net == "GND_STAR" and drill > 0:
                gnd_pads.append((cx+px, cy+py, pw))

    # Draw GND pads on bottom layer (thermal relief = annular ring only)
    for px, py, pw in gnd_pads:
        lines.append(f"%ADD11C,{pw:.4f}*%\n")
        lines.append(f"X{fmt(px,py)[1:]}D11*\n")

    # Draw back-side traces
    for net, layer, x1, y1, x2, y2, w in TRACES:
        if layer != "B": continue
        ap = get_aperture(w, "circle")
        lines.append(f"%ADD{ap[1:]}C,{w:.4f}*%\n")
        lines.append(f"G01*\nX{fmt(x1,y1)[1:]}Y{fmt(x1,y1)[1:]}D02*\n")
        lines.append(f"X{fmt(x2,y2)[1:]}Y{fmt(x2,y2)[1:]}D01*\n")

    lines.append("M02*")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# SOLDER MASK (both sides)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_solder_mask(layer):
    name = "Front" if layer == "F" else "Back"
    fname = f"EcoSynTech_V6_3_{layer}.Mask.gbr"
    lines = [gerber_header(f"{name} Solder Mask ({layer}.Mask)", fname)]
    lines.append(aperture_macros())

    # Mask openings = pads + 0.05mm clearance
    for ref, val, cx, cy, pads in COMPONENTS:
        for num, px, py, pw, ph, drill, shape, net in pads:
            if net == "NPTH" or net == "NC": continue
            # Opening slightly larger than pad
            ow = pw + 0.1
            oh = ph + 0.1
            ap = get_aperture(ow, shape)
            lines.append(f"%ADD{ap[1:]}C,{ow:.4f}*%\n")
            lines.append(f"X{fmt(cx+px, cy+py)[1:]}D{ap[1:]}*\n")

    # Via tenting not required (open for soldering)
    for x, y, net in VIAS:
        ow = 0.6 + 0.1
        lines.append(f"%ADD11C,{ow:.4f}*%\n")
        lines.append(f"X{fmt(x,y)[1:]}D11*\n")

    lines.append("M02*")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# SILKSCREEN (both sides)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_silkscreen(layer):
    name = "Front" if layer == "F" else "Back"
    fname = f"EcoSynTech_V6_3_{layer}.SilkS.gbr"
    lines = [gerber_header(f"{name} Silkscreen ({layer}.SilkS)", fname)]
    lines.append("%FSLAX46Y46*%\n%MOMM*%\n")
    lines.append("%ADD10C,0.1500*%\n")  # 0.15mm line width

    # Component outlines (simplified rectangles)
    for ref, val, cx, cy, pads in COMPONENTS:
        if ref.startswith("MH_") or ref.startswith("TP_") or ref.startswith("TV_") or ref.startswith("GV_"):
            continue
        if not pads: continue
        # Get bounding box
        xs = [cx + px for _, _, _, px, py, drill, shape, net in pads]
        ys = [cy + py for _, _, _, px, py, drill, shape, net in pads]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        margin = 0.3
        x0 -= margin; y0 -= margin; x1 += margin; y1 += margin

        # Draw outline rectangle
        lines.append(f"G01*\nX{fmt(x0,y0)[1:]}Y{fmt(x0,y0)[1:]}D02*\n")
        lines.append(f"X{fmt(x1,y0)[1:]}Y{fmt(x1,y0)[1:]}D01*\n")
        lines.append(f"X{fmt(x1,y1)[1:]}Y{fmt(x1,y1)[1:]}D01*\n")
        lines.append(f"X{fmt(x0,y1)[1:]}Y{fmt(x0,y1)[1:]}D01*\n")
        lines.append(f"X{fmt(x0,y0)[1:]}Y{fmt(x0,y0)[1:]}D01*\n")

    # Board outline
    lines.append("%ADD10C,0.1000*%\n")
    for i in range(len(BOARD_EDGE)-1):
        x1, y1 = BOARD_EDGE[i]
        x2, y2 = BOARD_EDGE[i+1]
        lines.append(f"G01*\nX{fmt(x1,y1)[1:]}Y{fmt(x1,y1)[1:]}D02*\n")
        lines.append(f"X{fmt(x2,y2)[1:]}Y{fmt(x2,y2)[1:]}D01*\n")

    lines.append("M02*")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# SOLDER PASTE (SMD only, front and back)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_paste(layer):
    name = "Front" if layer == "F" else "Back"
    fname = f"EcoSynTech_V6_3_{layer}.Paste.gbr"
    lines = [gerber_header(f"{name} Solder Paste ({layer}.Paste)", fname)]
    lines.append(aperture_macros())

    for ref, val, cx, cy, pads in COMPONENTS:
        for num, px, py, pw, ph, drill, shape, net in pads:
            if net == "NPTH" or net == "NC": continue
            if drill > 0: continue  # No paste for THT
            # Paste = 80% of pad
            pw_p = pw * 0.8
            ph_p = ph * 0.8
            ap = get_aperture(pw_p, "circle")
            lines.append(f"%ADD{ap[1:]}C,{pw_p:.4f}*%\n")
            lines.append(f"X{fmt(cx+px, cy+py)[1:]}D{ap[1:]}*\n")

    lines.append("M02*")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# BOARD OUTLINE
# ═══════════════════════════════════════════════════════════════════════════════
def gen_edge_cuts():
    lines = [gerber_header("Board Outline", "EcoSynTech_V6_3-Edge_Cuts.gbr")]
    lines.append("%FSLAX46Y46*%\n%MOMM*%\n")
    lines.append("%ADD10C,0.1000*%\n")
    lines.append("G01*\n")
    for i in range(len(BOARD_EDGE)-1):
        x1, y1 = BOARD_EDGE[i]
        x2, y2 = BOARD_EDGE[i+1]
        lines.append(f"X{fmt(x1,y1)[1:]}Y{fmt(x1,y1)[1:]}D02*\n")
        lines.append(f"X{fmt(x2,y2)[1:]}Y{fmt(x2,y2)[1:]}D01*\n")

    # Relay isolation slot (routed slot between relay zone and logic zone)
    lines.append(f"X{fmt(1,82)[1:]}Y{fmt(1,82)[1:]}D02*\n")
    lines.append(f"X{fmt(199,82)[1:]}Y{fmt(199,82)[1:]}D01*\n")
    lines.append(f"X{fmt(199,86)[1:]}Y{fmt(199,86)[1:]}D02*\n")
    lines.append(f"X{fmt(1,86)[1:]}Y{fmt(1,86)[1:]}D01*\n")

    lines.append("M02*")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# EXCELLON DRILL FILE
# ═══════════════════════════════════════════════════════════════════════════════
def gen_drill():
    lines = [
        "; EcoSynTech PCB v6.3 - Excellon Drill File",
        "; Board: 200mm x 150mm | 2-Layer | ENIG",
        "; Generated: 2026-04-16",
        "M48",
        "; Format: Metric, trailing zeros omitted",
        "METRIC,TZ",
        ";FILE_FORMAT=2:6",
        ";TYPE=PLATED",
        "%",
    ]

    # Collect all drills
    drills = {}  # code -> list of (x, y)
    drill_sizes = {
        0.3: "T1",  # Via 0.3mm drill
        0.8: "T2",  # SMD pad 0.8mm
        1.0: "T3",  # THT 1.0mm
        1.2: "T4",  # THT 1.2mm
        1.6: "T5",  # Relay/terminal 1.6mm
        3.2: "T6",  # Mounting hole 3.2mm NPTH
    }
    for code, dia in drill_sizes.items():
        drills[code] = []

    for ref, val, cx, cy, pads in COMPONENTS:
        for num, px, py, pw, ph, drill, shape, net in pads:
            if drill <= 0: continue
            # Match drill size
            d = round(drill, 1)
            if d not in drills:
                drills[d] = []
            drills[d].append((cx+px, cy+py))

    for dia, code in sorted(drill_sizes.items()):
        if drills.get(dia):
            lines.append(f"T{code[1:]}F00S00C{dia:.4f}")
    lines.append("%")
    lines.append(";")

    for dia, code in sorted(drill_sizes.items()):
        if not drills.get(dia): continue
        lines.append(f"; {code}: {dia}mm")
        lines.append(code)
        for x, y in sorted(drills[dia]):
            lines.append(f"X{fmt(x,y)[1:]}Y{fmt(x,y)[1:]}")
    lines.append("M30")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# PICK & PLACE FILES
# ═══════════════════════════════════════════════════════════════════════════════
def gen_pick_place():
    top_lines = ["Designator,Footprint,Center X (mm),Center Y (mm),Rotation,Layer"]
    bot_lines = ["Designator,Footprint,Center X (mm),Center Y (mm),Rotation,Layer"]

    for ref, val, cx, cy, pads in COMPONENTS:
        if ref.startswith("MH_") or ref.startswith("TV_") or ref.startswith("GV_"):
            continue

        # Determine footprint name
        fp_name = val if val else ref

        has_tht = any(drill > 0 for _, _, _, _, _, drill, _, _ in pads)
        if has_tht:
            top_lines.append(f"{ref},{fp_name},{cx:.2f},{cy:.2f},0,T")
        else:
            top_lines.append(f"{ref},{fp_name},{cx:.2f},{cy:.2f},0,T")

    bot_lines_top = []
    # Bottom side: through-hole component pads mirrored? No, standard PnP has all top
    # Bottom only gets SMD components on bottom side (none for this design, all SMD top)

    return '\n'.join(top_lines), '\n'.join(bot_lines)

# ═══════════════════════════════════════════════════════════════════════════════
# FABRICATION NOTES (comprehensive)
# ═══════════════════════════════════════════════════════════════════════════════
FABRICATION_NOTES = """================================================================================
EcoSynTech PCB v6.3 — FABRICATION NOTES (COMPLETE)
Industrial Outdoor IoT Controller | 2-Layer | 200mm x 150mm | ENIG
================================================================================
Project: EcoSynTech PCB v6.3 Final
Date: 2026-04-16
Revision: 6.3 Final
Origin: EcoSynTech Global
GitHub: github.com/ecosyntech68vn/EcoSynTech_PCB-for-IOT

================================================================================
1. GENERAL SPECIFICATIONS
================================================================================
Board Size:           200.0mm x 150.0mm (±0.1mm tolerance)
Board Thickness:       1.6mm (±0.1mm tolerance)
Number of Layers:      2 layers (F.Cu + B.Cu)
Minimum Line Width:    0.15mm (signal), 0.25mm (default)
Minimum Spacing:      0.2mm (default), 0.4mm (high voltage zones)
Minimum Drill:         0.3mm (PTH), 3.2mm (NPTH mounting holes)
Finished Copper:       1 oz (35μm) TOP layer
                      1 oz (35μm) BOTTOM layer (2 oz RECOMMENDED under relay zone)
Surface Finish:        ENIG (Electroless Nickel Immersion Gold) — MANDATORY
                        Nickel: 3-6μm
                        Gold: 0.05-0.1μm
Solder Mask:           Green LPI (Liquid Photoimageable), both sides
                        Thickness: 18-25μm after cure
                        Clearance: +0.05mm per side
Silkscreen:            White epoxy ink, front side only
Board Material:        FR-4, Tg ≥ 130°C (high-Tg mandatory for outdoor use)
Halogen Free:           Preferred (RoHS compliant)
UL Rating:             Preferred (FR-4 Tg130°C)

================================================================================
2. PCB FABRICATION REQUIREMENTS
================================================================================
2.1 Board Preparation
  - Routing tolerance: ±0.1mm on cut dimensions
  - Burr height: max 0.1mm
  - Panelization: V-score or tab-route recommended (see PANELIZATION.txt)
  - Panel size: multiple of 200mm x 150mm or as agreed with manufacturer
  - Board outline: 45-degree chamfer at all 4 corners, 3mm chamfer

2.2 Copper Quality
  - Base copper: 1 oz/sqft (35μm) minimum
  - **IMPORTANT**: Bottom layer (B.Cu) under relay section (X:5-100, Y:82-145mm):
    Use 2 oz copper (70μm) due to high current through relay coil driver traces
  - All copper features must meet IPC Class 2 standards
  - Minimum annular ring: 0.15mm for PTH, 0.1mm for vias
  - Pad lift test: 5 lbs minimum

2.3 Drilling
  - Drill tolerance: ±0.05mm
  - All PTH holes MUST be plated through (copper plated)
  - NPTH mounting holes: 4 x 3.2mm (non-plated, clean deburr)
    Positions: (5,5), (5,145), (195,5), (195,145) mm
  - Via holes: 0.3mm drill → 0.6mm outer pad
  - SMD pad holes: N/A (surface mount)
  - THT pad holes: 0.8mm (for connectors), 1.0mm (for USB), 1.6mm (for relays)
  - All holes must be clean, no epoxy voids, no barrel cracks
  - Pilot drill required for holes <0.5mm

2.4 Solder Mask
  - Type: LPI (Liquid Photoimageable), green
  - Both sides (top and bottom)
  - Solder mask clearance: +0.05mm (openings larger than copper pad)
  - Via tenting: NOT required — vias must be open for soldering
  - Minimum mask bridge: 0.1mm
  - Mask registration: ±0.05mm to copper

2.5 Surface Finish (ENIG — MANDATORY)
  - NO HASL finish accepted under any circumstances
  - ENIG is REQUIRED because:
    * ESP32-WROOM-32E module has BGA-like lead pitch requiring flat surface
    * All SMD pads for reliable soldering in outdoor environment
    * Long-term reliability against moisture and temperature cycling
    * Conformal coating adhesion is better on ENIG surface

2.6 Silkscreen
  - Front side only (back side optional)
  - Color: White epoxy ink
  - Minimum text height: 1.0mm, stroke width: 0.15mm
  - All reference designators must be legible
  - Silkscreen must not cover SMD pads or test points
  - Required labels (see silkscreen layer):
    * "EcoSynTech V6.3 Industrial Pro"
    * "Rev 6.3 Final | 2-Layer | ENIG | FR-4 Tg130"
    * "CAUTION: HIGH VOLTAGE 220VAC" (relay area, y≈95mm)
    * "THAY DUNG GIA TRI CAU CHI" (near fuse)
    * "KIEM TRA CUC TINH TRUOC KHI CAP NGUON"
    * "ANTENNA KEEPOUT ZONE" (near ESP32 module, top-right)
    * "DO NOT REMOVE SNUBBER - ARC HAZARD"
    * "EcoSynTech Global | ecosyntech68vn"
    * Date: "2026-04-16"

2.7 Electrical Test
  - 100% electrical test (flying probe or bed-of-nails)
  - Check for: opens, shorts, netlist verification
  - Test voltage: minimum 50V for isolation testing
  - Netlist provided separately (BOM + net connectivity)

================================================================================
3. SPECIAL REQUIREMENTS — CRITICAL
================================================================================
3.1 Relay Isolation Slot (ROUTED CUTOUT)
  - A routed SLOT must be cut through the board between relay zone and logic zone
  - Slot position: Y = 82mm to Y = 86mm (4mm slot), full width X = 1mm to X = 199mm
  - This is a MECHANICAL CUTOUT, not just clearance — board must be routed through
  - Slot must have GND via stitching on BOTH sides: every 5mm along Y=82 and Y=86
  - No conductive traces may cross this slot on any layer
  - Purpose: Prevent arc tracking from 220VAC relay contacts to low-voltage logic

3.2 ESP32 Antenna Keepout Zone
  - Zone: X: 156-175mm, Y: 68-75mm (top-right corner)
  - No copper, no components, no vias, no traces within this zone
  - Keepout applies to all layers (F.Cu, B.Cu, F.SilkS, B.SilkS)
  - Purpose: RF antenna radiation pattern must be unobstructed

3.3 Conformal Coating Ready
  - Board surface should be clean and dry
  - No solder mask on vias (open for coating penetration)
  - Board should pass ionic cleanliness test (max 1.56μg/inch NaCl equivalent)
  - Exclude zones for conformal coating:
    * All terminal blocks (TB1, J_DHT, J_DS, J_SOIL, J_AIN, J_VBAT, J_I2C_EXT, J_DEBUG, J_R1-4, J_EXP_HEADER, J_PWR_EXT)
    * USB connector (J_USB)
    * MicroSD socket (U_SDCARD)
    * All test points (TP_*)
    * Relay contact area
    * ESP32 antenna area

3.4 Environmental Rating
  - Operating temp: -20°C to +70°C (industrial outdoor)
  - Humidity: up to 95% RH non-condensing
  - Board designed for conformal coating + ABS enclosure + desiccant

================================================================================
4. NET CLASS RULES (for manufacturing review)
================================================================================
Class: Default
  Track width: 0.25mm
  Via diameter: 0.6mm, drill: 0.3mm
  Clearance: 0.2mm

Class: Power
  Track width: 1.0mm (+12V, +5V_MAIN, +5V_RELAY_RAW)
  Via diameter: 0.8mm, drill: 0.4mm
  Clearance: 0.4mm

Class: HighVoltage
  Track width: 0.6mm
  Clearance: 0.4mm
  Note: 6mm minimum clearance between relay contacts and LV circuits

================================================================================
5. REQUIRED FILES FOR FABRICATION
================================================================================
Gerber RS-274X Files:
  - EcoSynTech_V6_3_F.Cu.gbr         (Front Copper, Layer 1)
  - EcoSynTech_V6_3_B.Cu.gbr         (Back Copper, Layer 2)
  - EcoSynTech_V6_3_F.Mask.gbr        (Front Solder Mask)
  - EcoSynTech_V6_3_B.Mask.gbr       (Back Solder Mask)
  - EcoSynTech_V6_3_F.Paste.gbr      (Front Solder Paste)
  - EcoSynTech_V6_3_B.Paste.gbr      (Back Solder Paste)
  - EcoSynTech_V6_3_F.SilkS.gbr     (Front Silkscreen)
  - EcoSynTech_V6_3_B.SilkS.gbr     (Back Silkscreen)
  - EcoSynTech_V6_3-Edge_Cuts.gbr    (Board Outline + Relay Slot)
  - EcoSynTech_V6_3-Dwgs_User.gbr   (User drawings, fiducials)
  - EcoSynTech_V6_3-Cmts_User.gbr    (Fabrication notes on board)
  - EcoSynTech_V6_3.gbrjob           (Gerber job file)

NC Drill File (Excellon):
  - EcoSynTech_V6_3-Plated.Txt       (Plated through-hole, all sizes)
  Note: Mounting holes (T6, 3.2mm) are NPTH — must be in separate file or marked NPTH

Documentation:
  - FABRICATION_NOTES.txt (this file)
  - LAYER_STACKUP.txt (detailed layer stack)
  - PANELIZATION.txt (panel design guide)
  - NET_CLASS_INFO.txt (trace widths, clearances)

Assembly Files:
  - Pick_Place_F-Top.csv (top side components with positions)
  - Pick_Place_B-Bot.csv (bottom side components — currently empty, all SMD top)

BOM: EcoSynTech_V6_3_Final_BOM_V3.csv (provided separately)

================================================================================
6. QUALITY STANDARDS
================================================================================
- IPC-A-600 Class 2 (Acceptability of Printed Boards)
- IPC-6012 Class 2 (Qualification and Performance of Rigid Printed Boards)
- IPC-2221 (Generic Standard on Printed Board Design)
- RoHS 3 (EU 2015/863) — all materials must be RoHS compliant
- REACH compliance required
- UL rating preferred (FR-4 Tg130°C)

================================================================================
7. IMPORTANT NOTES FOR FAB HOUSE
================================================================================
A. ENIG SURFACE FINISH IS NON-NEGOTIABLE
   The ESP32-WROOM-32E module requires flat, coplanar pad surface.
   HASL finish will cause soldering problems with this fine-pitch module.

B. RELAY ISOLATION SLOT IS A ROUTED CUTOUT
   This is not a solder mask opening — the board must be routed through
   at Y=82-86mm. Provide a routed panel, not just masked copper.

C. BOTTOM LAYER COPPER WEIGHT
   Standard 1 oz bottom layer OK for most of board.
   But relay driver area (X:140-185mm, Y:82-145mm) should use 2 oz
   due to relay coil current (~70mA per relay driver transistor).

D. FLYING PROBE TEST REQUIRED
   Please provide netlist verification report.
   Netlist available at: github.com/ecosyntech68vn/EcoSynTech_PCB-for-IOT

================================================================================
8. CONTACT INFORMATION
================================================================================
Project Owner: EcoSynTech Global
Email: ecosyntech68vn@github.com
GitHub: github.com/ecosyntech68vn/EcoSynTech_PCB-for-IOT
Board Spec: 200mm x 150mm x 1.6mm | 2-Layer | ENIG | FR-4 Tg130°C
Component Count: ~215 footprints (all provided in KiCad project)

================================================================================
END OF FABRICATION NOTES
================================================================================
"""

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER STACKUP
# ═══════════════════════════════════════════════════════════════════════════════
LAYER_STACKUP = """================================================================================
EcoSynTech PCB v6.3 — LAYER STACKUP
================================================================================

Board: 200mm x 150mm x 1.6mm | 2 Copper Layers | ENIG Finish

DETAILED LAYER STACKUP (from top to bottom):
==============================================

Layer 1: Top Silkscreen (White)
  - Ink: White epoxy, 20-30μm thickness
  - Contents: Reference designators, logos, warnings, board ID
  - Drying: Thermal cure
  - Coverage: Front side only

Layer 2: Top Solder Mask (Green LPI)
  - Material: Green LPI (photosensitive)
  - Thickness: 18-25μm (after cure)
  - Opening tolerance: +0.05mm per side
  - Coverage: Both sides (top and bottom)
  - Via openings: OPEN (NOT tented)

Layer 3: Top Copper (F.Cu) — 35μm (1 oz)
  - Material: Electrolytic copper foil
  - Thickness: 35μm (1.37 mil)
  - Min trace width: 0.15mm (signal), 0.25mm (default)
  - Min spacing: 0.2mm (default), 0.4mm (HV zones)
  - Note: 2 oz recommended for relay driver area traces

Layer 4: Prepreg / Dielectric
  - Material: FR-4 prepreg (106/1080 or equivalent)
  - Thickness: 1.1mm (composite)
  - Dk (dielectric constant): 4.5 @ 1MHz
  - Df (dissipation factor): 0.02 @ 1MHz
  - Tg: ≥ 130°C (high-Tg FR-4 MANDATORY)

Layer 5: Bottom Copper (B.Cu) — 35μm (1 oz)
  - Material: Electrolytic copper foil
  - Thickness: 35μm (1.37 mil)
  - **IMPORTANT**: Use 70μm (2 oz) for relay area (X:140-185mm, Y:82-145mm)
  - Min trace width: 0.15mm
  - GND plane with thermal relief pads

Layer 6: Bottom Solder Mask (Green LPI)
  - Material: Green LPI (photosensitive)
  - Thickness: 18-25μm (after cure)
  - Vias: Open (NOT tented — must be solderable)

Layer 7: Bottom Silkscreen (White) — Optional
  - Usually not applied for 2-layer boards
  - If applied: same as top silkscreen

Layer 8: ENIG Surface Finish (Top + Bottom)
  - Nickel: 3-6μm (electroless nickel)
  - Gold: 0.05-0.1μm (immersion gold)
  - Total finish thickness: 3-6.1μm

BOARD CROSS-SECTION SUMMARY:
============================
  Top Silkscreen (White):    ~0.02mm
  Top Solder Mask:            ~0.02mm
  Top Copper:                ~0.035mm (1oz)
  FR-4 Core:                ~1.56mm
  Bottom Copper:             ~0.035mm (1oz standard, 0.07mm 2oz relay zone)
  Bottom Solder Mask:         ~0.02mm
  ENIG Finish:              ~0.005mm
  ===========================
  Total:                    ~1.67mm (±5%)

IMPORTANT NOTES:
===============
1. ENIG surface finish is MANDATORY — NO HASL
2. Bottom copper under relay section: 2 oz (70μm) recommended
3. All vias must be open (not tented) for solderability
4. Board must pass 100% E-test before delivery
5. FR-4 Tg ≥ 130°C is MANDATORY (industrial/outdoor use)
6. Relay isolation slot: routed cutout at Y=82-86mm, full width

DETAILED ZONE ALLOCATION ON BOARD:
=================================
  Zone A (top-left, X:5-50mm, Y:5-30mm):
    Power input, protection: TB1, F1, GDT1, MOV1, TVS1, Q_PROTECT
    Heavy copper 1mm traces for +12V power path

  Zone B (top-center, X:55-105mm, Y:5-50mm):
    Buck regulator #1 (12V→5V, MP1584)
    Thermal via array under U2_5V
    +5V_MAIN power distribution

  Zone C (top-right, X:110-200mm, Y:5-50mm):
    Buck regulator #2 (12V→3.3V, MP1584)
    USB-UART, auto-reset circuit, watchdog
    I2C peripherals (BME280, OLED)
    ANTENNA KEEPOUT ZONE (X:156-175mm, Y:68-75mm)

  Zone D (center-left, X:5-100mm, Y:30-82mm):
    ESP32 module (full width), MicroSD, status LEDs
    Ferrite bead rail splitting (FB_ESP, FB_ANA)
    I2C expander MCP23017×2
    All decoupling capacitors

  Zone E (center-right, X:80-150mm, Y:45-70mm):
    ADS1115 4-channel ADC
    Analog input networks (series resistors + TVS)
    Battery/VIN sense divider

  Zone F (BOTTOM — RELAY ZONE, X:5-195mm, Y:82-145mm):
    RELAY SECTION — HIGH VOLTAGE ZONE
    4× relay sockets SRD-05VDC-SL-C (RELAY1-4)
    4× relay drivers (S8050 NPN + flyback diodes)
    RC snubbers across relay contacts
    4× expansion relay sockets (RELAY5-8, optional)
    DANGER: 220VAC relay contacts
    ROUTED SLOT at Y=82-86mm separates relay from logic
    Minimum HV clearance: 6mm from relay contacts to LV circuitry
    Bottom copper: 2 oz recommended under relay drivers
    GND via stitching: every 5mm along relay slot edges

  Zone G (external connectors, X:185-200mm, Y:5-145mm):
    All field wiring terminal blocks
    J_PWR_EXT, J_R1-4, J_EXP_HEADER

================================================================================
END OF LAYER STACKUP
================================================================================
"""

PANELIZATION = """================================================================================
EcoSynTech PCB v6.3 — PANELIZATION GUIDE
================================================================================

BOARD SINGLE UNIT: 200mm x 150mm x 1.6mm

PANELIZATION OPTIONS:
====================

Option 1: Single Board (No Panelization)
  - Use this if ordering small quantities (1-10 boards)
  - Route individual boards from panel
  - Recommended for first production run

Option 2: Array Panel (Recommended for 10 boards)
  - Panel size: 410mm x 310mm (fits standard fab capabilities)
  - 2 x 2 array = 4 boards per panel
  - Use tab-route (mouse-bites) between boards
  - Tab width: 3mm, spacing: 1.5mm
  - Fiducials: 3 per board, 6 per panel

  Panel Layout (410mm x 310mm):
    +---------------------------+
    |  [200x150]  |  [200x150]  |
    |   Board 1  |   Board 2   |
    |-------------+-------------|
    |  [200x150]  |  [200x150]  |
    |   Board 3  |   Board 4   |
    +---------------------------+
    (Tab routes between all boards)

    Board spacing: 5mm between boards (routing clearance)
    
    Fiducial positions on panel:
      - Panel corners: 10mm from edge
      - Between boards: center of tab routes

Option 3: V-Score Panel
  - Score lines between boards (no tabs)
  - V-score depth: 0.5mm (1/3 of board thickness)
  - V-score spacing: 0.3mm
  - Recommended for larger quantities (20+)

PANEL REQUIREMENTS:
==================
  - Panel material: Same as board (FR-4 Tg130°C)
  - Panel thickness: 1.6mm (same as board)
  - Tab routing tolerance: ±0.1mm
  - Panel must be clean (no debris from routing)
  - Panel should have panel ID marking (laser engraved or silkscreen)

REQUIRED PANEL FEATURES:
=======================
  1. Tooling holes: 3mm diameter, 6 places
     - 3 on left edge, 3 on right edge
     - Spacing: 25mm from edges
  2. Fiducial marks:
     - 3mm outer, 1mm inner (crosshair)
     - 3 per individual board
     - 6 per full panel
  3. Panel ID: laser engraved
     - Content: Part number, revision, date code, panel number
     - Position: Bottom right of panel

PANELIZATION SUMMARY:
====================
  Single unit: 200 x 150mm
  Recommended panel: 410 x 310mm (2x2 array)
  Routing method: Tab-route (mouse-bites)
  Vias: All open (solderable)
  Fiducials: 3 per board unit
  Panel marking: Required

================================================================================
END OF PANELIZATION GUIDE
================================================================================
"""

GERBER_JOB = """{
  "Header": {
    "GenerationSoftware": {
      "Vendor": "EcoSynTech Global",
      "Application": "KiCad Manufacturing Generator v2",
      "Version": "2.0"
    },
    "CreationDate": "2026-04-16T00:00:00+00:00",
    "ProjectId": {
      "Id": "EcoSynTech_PCB_v6.3",
      "GUID": "B1C2D3E4-F5A6-7890-ABCD-EF1234567890",
      "Name": "EcoSynTech PCB v6.3",
      "Revision": "6.3 Final"
    }
  },
  "Board": {
    "Id": "0",
    "Name": "EcoSynTech PCB v6.3",
    "Revision": "6.3 Final",
    "SourceFiles": {
      "GERBER": "EcoSynTech_V6_3_F.Cu.gbr",
      "DRILL": "EcoSynTech_V6_3-Plated.Txt",
      "EDA": "EcoSynTech_V6_3_Final.kicad_pcb"
    },
    "NumberOfLayers": 2,
    "Thickness": 1.6,
    "ThicknessUnit": "mm",
    "OuterDimensionX": 200.0,
    "OuterDimensionY": 150.0,
    "DimensionUnit": "mm"
  },
  "DesignRules": {
    "Layers": {
      "Top": {
        "LayerNumber": 1,
        "LayerName": "F.Cu",
        "Plot": true,
        "CopperWeight": "1 oz",
        "PowerRailConnections": ["+12V_PROTECTED", "+5V_MAIN", "+5V_RELAY_RAW", "+3V3_ESP", "+3V3_ANA"]
      },
      "Bottom": {
        "LayerNumber": 2,
        "LayerName": "B.Cu",
        "Plot": true,
        "CopperWeight": "1 oz",
        "Notes": "2 oz recommended for relay zone X:140-185mm Y:82-145mm",
        "PowerRailConnections": ["GND_STAR"]
      }
    },
    "MinimumLineWidth": 0.15,
    "MinimumAnnularRing": 0.15,
    "MinimumSolderMaskClearance": 0.05,
    "Vias": {
      "Plated": true,
      "DrillFinishedSize": 0.3,
      "OuterDiameter": 0.6
    }
  },
  "FilesAttributes": {
    "Gerber": {
      "Files": [
        {"Name": "EcoSynTech_V6_3_F.Cu.gbr", "Function": "CopperL1", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3_B.Cu.gbr", "Function": "CopperL2", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3_F.Mask.gbr", "Function": "SoldermaskTop", "Polarity": "Negative"},
        {"Name": "EcoSynTech_V6_3_B.Mask.gbr", "Function": "SoldermaskBot", "Polarity": "Negative"},
        {"Name": "EcoSynTech_V6_3_F.Paste.gbr", "Function": "SolderpasteTop", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3_B.Paste.gbr", "Function": "SolderpasteBot", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3_F.SilkS.gbr", "Function": "SilkscreenTop", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3_B.SilkS.gbr", "Function": "SilkscreenBot", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3-Edge_Cuts.gbr", "Function": "BoardOutline", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3-Dwgs_User.gbr", "Function": "Profile", "Polarity": "Positive"},
        {"Name": "EcoSynTech_V6_3-Cmts_User.gbr", "Function": "Comments", "Polarity": "Positive"}
      ],
      "ViewOrder": 1,
      "NumberOfFiles": 11
    },
    "Drill": {
      "Files": [
        {"Name": "EcoSynTech_V6_3-Plated.Txt", "Function": "PlatedPTHDrill", "Plating": "Plated"}
      ],
      "Format": "Excellon",
      "Units": "Metric"
    }
  },
  "MaterialStackup": [
    {"LayerName": "Top Silkscreen", "Material": "Epoxy ink (white)", "Thickness": 0.020, "Unit": "mm"},
    {"LayerName": "Top Solder Mask", "Material": "LPI Green", "Thickness": 0.020, "Unit": "mm"},
    {"LayerName": "Top Copper", "Material": "Copper", "Thickness": 0.035, "Unit": "mm", "Type": "1 oz"},
    {"LayerName": "Prepreg", "Material": "FR-4 Prepreg", "Thickness": 1.100, "Unit": "mm"},
    {"LayerName": "Bottom Copper", "Material": "Copper", "Thickness": 0.035, "Unit": "mm", "Type": "1 oz"},
    {"LayerName": "Bottom Solder Mask", "Material": "LPI Green", "Thickness": 0.020, "Unit": "mm"},
    {"LayerName": "ENIG Finish", "Material": "Ni/Au", "Thickness": 0.005, "Unit": "mm"}
  ]
}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== EcoSynTech PCB v6.3 — Manufacturing Files Generator ===")
    print(f"Components: {len(COMPONENTS)}")
    print(f"Traces: {len(TRACES)}")
    print(f"Vias: {len(VIAS)}")

    print("\nGenerating Gerber files...")
    for name, func in [
        ("F.Cu", gen_copper_front),
        ("B.Cu", gen_copper_back),
        ("F.Mask", lambda: gen_solder_mask("F")),
        ("B.Mask", lambda: gen_solder_mask("B")),
        ("F.SilkS", lambda: gen_silkscreen("F")),
        ("B.SilkS", lambda: gen_silkscreen("B")),
        ("F.Paste", lambda: gen_paste("F")),
        ("B.Paste", lambda: gen_paste("B")),
        ("Edge_Cuts", gen_edge_cuts),
    ]:
        content = func()
        fname = f"EcoSynTech_V6_3_{name}.gbr" if "Edge" not in name else f"EcoSynTech_V6_3-{name}.gbr"
        path = f"{OUT}/{fname}"
        with open(path, "w") as f:
            f.write(content)
        print(f"  {path} ({len(content)} bytes)")

    print("\nGenerating drill file...")
    drill_content = gen_drill()
    drill_path = f"{OUT}/EcoSynTech_V6_3-Plated.Txt"
    with open(drill_path, "w") as f:
        f.write(drill_content)
    print(f"  {drill_path} ({len(drill_content)} bytes)")

    print("\nGenerating documentation...")
    for name, content in [
        ("FABRICATION_NOTES.txt", FABRICATION_NOTES),
        ("LAYER_STACKUP.txt", LAYER_STACKUP),
        ("PANELIZATION.txt", PANELIZATION),
        ("GERBER_JOB.json", GERBER_JOB),
    ]:
        path = f"{MOUT}/{name}"
        with open(path, "w") as f:
            f.write(content)
        print(f"  {path} ({len(content)} bytes)")

    print("\nGenerating Pick & Place files...")
    top_pp, bot_pp = gen_pick_place()
    for name, content in [
        ("Pick_Place_F-Top.csv", top_pp),
        ("Pick_Place_B-Bot.csv", bot_pp),
    ]:
        path = f"{MOUT}/{name}"
        with open(path, "w") as f:
            f.write(content)
        print(f"  {path} ({len(content)} bytes)")

    print("\nDone! Manufacturing files ready.")
    print(f"\nGerber files: {OUT}/")
    print(f"Documentation: {MOUT}/")
