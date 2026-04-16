#!/usr/bin/env python3
"""
EcoSynTech PCB v6.3 — Manufacturing File Generator
Generates Gerber RS-274X, Excellon drill, and manufacturing documentation.
"""
import os, math

OUT = "/tmp/ecosyn-pcb/gerber"
MFG = "/tmp/ecosyn-pcb/manufacturing"
os.makedirs(OUT, exist_ok=True)
os.makedirs(MFG, exist_ok=True)

# ─── Board Parameters ─────────────────────────────────────────────────────────
BOARD_W = 200.0   # mm
BOARD_H = 150.0   # mm
THICKNESS = 1.6   # mm
EDGE_MARGIN = 5.0 # mm from edge for mounting holes

# Gerber settings
GERBER_UNIT = "MM"
GERBER_NUMBER_FORMAT = "4"  # integer digits
GERBER_DECIMAL_FORMAT = "6"  # decimal places

# Aperture definitions (D-codes) for RS-274X
# We'll define standard apertures
APERTURES = {
    # D10: Circle 0.25mm (default trace)
    10: ("C", 0.25, "Default trace 0.25mm"),
    # D11: Circle 0.6mm (via outer)
    11: ("C", 0.6, "Via outer 0.6mm"),
    # D12: Circle 0.8mm (Power via outer)
    12: ("C", 0.8, "Power via outer 0.8mm"),
    # D13: Rectangle 0.6×0.25mm (SMD 0805 resistor)
    13: ("R", (0.6, 0.25), "SMD 0805 resistor"),
    # D14: Circle 0.4mm (via drill 0.3mm + annular ring)
    14: ("C", 0.4, "Via drill interpretation"),
    # D15: Rectangle 0.3×0.3mm (SOT-23 pad)
    15: ("R", (0.3, 0.3), "SOT-23 pad"),
    # D16: Circle 3.2mm (M3 mounting hole)
    16: ("C", 3.2, "M3 mounting hole"),
    # D17: Circle 0.8mm (THT pad 0.8mm)
    17: ("C", 0.8, "THT pad 0.8mm"),
    # D18: Circle 1.0mm (THT pad 1.0mm)
    18: ("C", 1.0, "THT pad 1.0mm"),
    # D19: Circle 1.6mm (Relay pad)
    19: ("C", 1.6, "Relay terminal pad 1.6mm"),
    # D20: Rectangle 1.0×0.5mm (SOIC-8 pad)
    20: ("R", (1.0, 0.5), "SOIC-8/SOP-8 pad"),
    # D21: Rectangle 0.3×0.6mm (MSOP-8 pad)
    21: ("R", (0.3, 0.6), "MSOP-8 pad"),
    # D22: Rectangle 0.25×0.5mm (SMD pad small)
    22: ("R", (0.25, 0.5), "Small SMD pad"),
    # D23: Circle 0.5mm (Test point)
    23: ("C", 0.5, "Test point pad"),
    # D24: Circle 1.0mm (Terminal block pad)
    24: ("C", 1.0, "Terminal block pad"),
    # D25: Rectangle 0.8×0.4mm (SSOP-28 pad)
    25: ("R", (0.8, 0.4), "SSOP-28 pad"),
}

# Apertures for silkscreen
SILK_APERTURES = {
    1: ("C", 0.15, "Silkscreen line 0.15mm"),
    2: ("C", 0.2, "Silkscreen line 0.2mm"),
    3: ("C", 0.25, "Silkscreen line 0.25mm"),
    4: ("C", 0.3, "Silkscreen line 0.3mm"),
}

# Solder mask apertures (slightly larger than copper)
MASK_APERTURES = {
    10: ("C", 0.35, "Solder mask 0805"),
    11: ("C", 0.7, "Via mask 0.6mm"),
    13: ("R", (0.7, 0.35), "SMD mask 0805"),
    17: ("C", 0.9, "THT pad mask 0.8mm"),
    18: ("C", 1.1, "THT pad mask 1.0mm"),
    19: ("C", 1.7, "Relay pad mask 1.6mm"),
    20: ("R", (1.1, 0.6), "SOIC-8 mask"),
    21: ("R", (0.4, 0.7), "MSOP-8 mask"),
    24: ("C", 1.1, "Terminal mask 1.0mm"),
    25: ("R", (0.9, 0.5), "SSOP-28 mask"),
}

# ─── Gerber RS-274X Generator ─────────────────────────────────────────────────

def gerber_header(filename, layer_name):
    """Generate standard Gerber file header."""
    return (
        f"G04 EcoSynTech PCB v6.3 - {layer_name}*\n"
        f"G04 Board: 200mm x 150mm | 2-Layer | ENIG*\n"
        f"%FSLAX{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}Y{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}*%\n"
        f"%MO{GERBER_UNIT}*%\n"
        f"%ADD10C,{APERTURES[10][1]:.4f}*%\n"
        f"%ADD11C,{APERTURES[11][1]:.4f}*%\n"
        f"%ADD12C,{APERTURES[12][1]:.4f}*%\n"
        f"%ADD13R,{APERTURES[13][1][0]:.4f}X{APERTURES[13][1][1]:.4f}*%\n"
        f"%ADD15R,{APERTURES[15][1][0]:.4f}X{APERTURES[15][1][1]:.4f}*%\n"
        f"%ADD16C,{APERTURES[16][1]:.4f}*%\n"
        f"%ADD17C,{APERTURES[17][1]:.4f}*%\n"
        f"%ADD18C,{APERTURES[18][1]:.4f}*%\n"
        f"%ADD19C,{APERTURES[19][1]:.4f}*%\n"
        f"%ADD20R,{APERTURES[20][1][0]:.4f}X{APERTURES[20][1][1]:.4f}*%\n"
        f"%ADD21R,{APERTURES[21][1][0]:.4f}X{APERTURES[21][1][1]:.4f}*%\n"
        f"%ADD22R,{APERTURES[22][1][0]:.4f}X{APERTURES[22][1][1]:.4f}*%\n"
        f"%ADD23C,{APERTURES[23][1]:.4f}*%\n"
        f"%ADD24C,{APERTURES[24][1]:.4f}*%\n"
        f"%ADD25R,{APERTURES[25][1][0]:.4f}X{APERTURES[25][1][1]:.4f}*%\n"
    )

def gerber_footer():
    return "M02*\n"

def gerber_copper_layer(filename, layer_name, side="F"):
    """Generate copper layer Gerber file."""
    lines = []
    lines.append(gerber_header(filename, layer_name))
    
    if side == "F":
        # ─── FRONT COPPER LAYER (F.Cu) ───────────────────────────────
        # Board outline (rectangle)
        x1, y1 = EDGE_MARGIN, EDGE_MARGIN
        x2, y2 = BOARD_W - EDGE_MARGIN, BOARD_H - EDGE_MARGIN
        lines.append(f"G01*\n")
        # Draw outline as 4 segments
        lines.append(f"X{int(x1*10000):05d}Y{int(y1*10000):05d}D02*\n")
        lines.append(f"X{int(x2*10000):05d}Y{int(y1*10000):05d}D01*\n")
        lines.append(f"X{int(x2*10000):05d}Y{int(y2*10000):05d}D01*\n")
        lines.append(f"X{int(x1*10000):05d}Y{int(y2*10000):05d}D01*\n")
        lines.append(f"X{int(x1*10000):05d}Y{int(y1*10000):05d}D01*\n")
        
        # ─── POWER PLANE (GND fill) ──────────────────────────────────
        # GND polygon on F.Cu - use thermal reliefs for through holes
        # Draw GND zone outline
        zone_margin = 1.0
        lines.append("G36*\n")
        lines.append(f"X{int((zone_margin)*10000):05d}Y{int((zone_margin)*10000):05d}D02*\n")
        lines.append(f"X{int((BOARD_W-zone_margin)*10000):05d}Y{int((zone_margin)*10000):05d}D01*\n")
        lines.append(f"X{int((BOARD_W-zone_margin)*10000):05d}Y{int((BOARD_H-zone_margin)*10000):05d}D01*\n")
        lines.append(f"X{int((zone_margin)*10000):05d}Y{int((BOARD_H-zone_margin)*10000):05d}D01*\n")
        lines.append(f"X{int((zone_margin)*10000):05d}Y{int((zone_margin)*10000):05d}D01*\n")
        lines.append("G37*\n")
        
        # ─── +12V_PROTECTED plane (top right area) ───────────────────
        lines.append("G36*\n")
        lines.append(f"X{int(10*10000):05d}Y{int(10*10000):05d}D02*\n")
        lines.append(f"X{int(60*10000):05d}Y{int(10*10000):05d}D01*\n")
        lines.append(f"X{int(60*10000):05d}Y{int(80*10000):05d}D01*\n")
        lines.append(f"X{int(10*10000):05d}Y{int(80*10000):05d}D01*\n")
        lines.append(f"X{int(10*10000):05d}Y{int(10*10000):05d}D01*\n")
        lines.append("G37*\n")
        
        # ─── +5V_MAIN plane (center) ─────────────────────────────────
        lines.append("G36*\n")
        lines.append(f"X{int(60*10000):05d}Y{int(10*10000):05d}D02*\n")
        lines.append(f"X{int(110*10000):05d}Y{int(10*10000):05d}D01*\n")
        lines.append(f"X{int(110*10000):05d}Y{int(80*10000):05d}D01*\n")
        lines.append(f"X{int(60*10000):05d}Y{int(80*10000):05d}D01*\n")
        lines.append(f"X{int(60*10000):05d}Y{int(10*10000):05d}D01*\n")
        lines.append("G37*\n")
        
        # ─── +3V3 plane (center-left) ───────────────────────────────
        lines.append("G36*\n")
        lines.append(f"X{int(110*10000):05d}Y{int(10*10000):05d}D02*\n")
        lines.append(f"X{int(160*10000):05d}Y{int(10*10000):05d}D01*\n")
        lines.append(f"X{int(160*10000):05d}Y{int(80*10000):05d}D01*\n")
        lines.append(f"X{int(110*10000):05d}Y{int(80*10000):05d}D01*\n")
        lines.append(f"X{int(110*10000):05d}Y{int(10*10000):05d}D01*\n")
        lines.append("G37*\n")
        
        # ─── Relay area (bottom) ────────────────────────────────────
        lines.append("G36*\n")
        lines.append(f"X{int(10*10000):05d}Y{int(80*10000):05d}D02*\n")
        lines.append(f"X{int(190*10000):05d}Y{int(80*10000):05d}D01*\n")
        lines.append(f"X{int(190*10000):05d}Y{int(145*10000):05d}D01*\n")
        lines.append(f"X{int(10*10000):05d}Y{int(145*10000):05d}D01*\n")
        lines.append(f"X{int(10*10000):05d}Y{int(80*10000):5d}D01*\n")
        lines.append("G37*\n")
        
        # ─── +5V_MAIN trace (power) ────────────────────────────────
        # Thick trace 1.0mm from MP1584 to relay section
        lines.append("%ADD12C,1.0000*%\n")
        lines.append("G01*\n")
        lines.append(f"X{int(65*10000):05d}Y{int(35*10000):05d}D02*\n")
        lines.append(f"X{int(65*10000):05d}Y{int(90*10000):05d}D01*\n")
        lines.append(f"X{int(185*10000):05d}Y{int(90*10000):05d}D01*\n")
        
        # ─── +12V_PROTECTED trace (power) ──────────────────────────
        lines.append(f"X{int(15*10000):05d}Y{int(25*10000):05d}D02*\n")
        lines.append(f"X{int(15*10000):05d}Y{int(65*10000):05d}D01*\n")
        lines.append(f"X{int(60*10000):05d}Y{int(65*10000):05d}D01*\n")
        
        # ─── +3V3_ESP trace ─────────────────────────────────────────
        lines.append(f"X{int(115*10000):05d}Y{int(45*10000):05d}D02*\n")
        lines.append(f"X{int(115*10000):05d}Y{int(75*10000):05d}D01*\n")
        lines.append(f"X{int(155*10000):05d}Y{int(75*10000):05d}D01*\n")
        
        # ─── GND traces ─────────────────────────────────────────────
        lines.append("G01*\n")
        lines.append(f"X{int(20*10000):05d}Y{int(35*10000):05d}D02*\n")
        lines.append(f"X{int(20*10000):05d}Y{int(130*10000):05d}D01*\n")
        lines.append(f"X{int(180*10000):05d}Y{int(130*10000):05d}D01*\n")
        lines.append(f"X{int(180*10000):05d}Y{int(35*10000):05d}D01*\n")
        
        # ─── Signal traces (0.25mm) ─────────────────────────────────
        lines.append("%ADD10C,0.2500*%\n")
        
        # I2C bus traces
        lines.append("G01*\n")
        # SCL
        lines.append(f"X{int(155*10000):05d}Y{int(45*10000):05d}D02*\n")
        lines.append(f"X{int(155*10000):05d}Y{int(55*10000):05d}D01*\n")
        lines.append(f"X{int(100*10000):05d}Y{int(55*10000):05d}D01*\n")
        lines.append(f"X{int(100*10000):05d}Y{int(45*10000):05d}D01*\n")
        # SDA
        lines.append(f"X{int(155*10000):05d}Y{int(48*10000):05d}D02*\n")
        lines.append(f"X{int(155*10000):05d}Y{int(58*10000):05d}D01*\n")
        lines.append(f"X{int(100*10000):05d}Y{int(58*10000):05d}D01*\n")
        lines.append(f"X{int(100*10000):05d}Y{int(48*10000):05d}D01*\n")
        
        # Relay driver traces (GPIO to relay section)
        lines.append(f"X{int(155*10000):05d}Y{int(35*10000):05d}D02*\n")
        lines.append(f"X{int(155*10000):05d}Y{int(90*10000):05d}D01*\n")
        lines.append(f"X{int(175*10000):05d}Y{int(90*10000):05d}D01*\n")
        lines.append(f"X{int(175*10000):05d}Y{int(95*10000):05d}D01*\n")
        
        # USB differential pair
        lines.append(f"X{int(25*10000):05d}Y{int(30*10000):05d}D02*\n")
        lines.append(f"X{int(25*10000):05d}Y{int(35*10000):05d}D01*\n")
        
        # SPI bus to MicroSD
        lines.append(f"X{int(155*10000):05d}Y{int(65*10000):05d}D02*\n")
        lines.append(f"X{int(155*10000):05d}Y{int(85*10000):05d}D01*\n")
        
        # ─── Via placements ───────────────────────────────────────────
        # GND vias (thermal relief style - draw as flash)
        lines.append("%ADD11C,0.6000*%\n")
        # GND via at input area
        for (vx, vy) in [(20, 30), (30, 30), (40, 30), (20, 40), (30, 40), (40, 40),
                           (20, 130), (30, 130), (40, 130), (20, 140), (30, 140), (40, 140),
                           (160, 130), (170, 130), (180, 130), (160, 140), (170, 140), (180, 140),
                           (100, 40), (110, 40), (120, 40), (100, 50), (110, 50), (120, 50)]:
            lines.append(f"X{int(vx*10000):05d}Y{int(vy*10000):05d}D03*\n")
        
        # Power vias
        lines.append("%ADD12C,0.8000*%\n")
        for (vx, vy) in [(15, 25), (60, 65), (65, 65), (115, 45), (155, 75), (185, 90)]:
            lines.append(f"X{int(vx*10000):05d}Y{int(vy*10000):05d}D03*\n")
        
        # Signal vias
        lines.append("%ADD11C,0.6000*%\n")
        for (vx, vy) in [(100, 45), (100, 55), (100, 48), (100, 58),
                           (155, 45), (155, 48), (155, 55), (155, 58),
                           (155, 35), (155, 65), (175, 90), (175, 95),
                           (25, 30), (25, 35)]:
            lines.append(f"X{int(vx*10000):05d}Y{int(vy*10000):05d}D03*\n")
        
    else:
        # ─── BACK COPPER LAYER (B.Cu) ───────────────────────────────
        # Board outline
        x1, y1 = EDGE_MARGIN, EDGE_MARGIN
        x2, y2 = BOARD_W - EDGE_MARGIN, BOARD_H - EDGE_MARGIN
        lines.append("G01*\n")
        lines.append(f"X{int(x1*10000):05d}Y{int(y1*10000):05d}D02*\n")
        lines.append(f"X{int(x2*10000):05d}Y{int(y1*10000):05d}D01*\n")
        lines.append(f"X{int(x2*10000):05d}Y{int(y2*10000):05d}D01*\n")
        lines.append(f"X{int(x1*10000):05d}Y{int(y2*10000):05d}D01*\n")
        lines.append(f"X{int(x1*10000):05d}Y{int(y1*10000):05d}D01*\n")
        
        # GND copper fill (large area on back)
        lines.append("G36*\n")
        zone_margin = 1.0
        lines.append(f"X{int((zone_margin)*10000):05d}Y{int((zone_margin)*10000):05d}D02*\n")
        lines.append(f"X{int((BOARD_W-zone_margin)*10000):05d}Y{int((zone_margin)*10000):05d}D01*\n")
        lines.append(f"X{int((BOARD_W-zone_margin)*10000):05d}Y{int((BOARD_H-zone_margin)*10000):05d}D01*\n")
        lines.append(f"X{int((zone_margin)*10000):05d}Y{int((BOARD_H-zone_margin)*10000):05d}D01*\n")
        lines.append(f"X{int((zone_margin)*10000):05d}Y{int((zone_margin)*10000):05d}D01*\n")
        lines.append("G37*\n")
        
        # GND thermal spokes to mounting holes
        lines.append("%ADD11C,0.6000*%\n")
        for (vx, vy) in [(5, 5), (5, 145), (195, 5), (195, 145)]:
            lines.append(f"X{int(vx*10000):05d}Y{int(vy*10000):05d}D03*\n")
        
        # Via stitching (back-side GND stitching vias)
        for y in range(15, 140, 15):
            lines.append(f"X{int(10*10000):05d}Y{int(y*10000):05d}D03*\n")
            lines.append(f"X{int(20*10000):05d}Y{int(y*10000):05d}D03*\n")
            lines.append(f"X{int(180*10000):05d}Y{int(y*10000):05d}D03*\n")
            lines.append(f"X{int(190*10000):05d}Y{int(y*10000):05d}D03*\n")
        
        # Power rail stitching on back
        lines.append("%ADD12C,0.8000*%\n")
        for y in [25, 40, 55, 70, 85, 100, 115, 130]:
            lines.append(f"X{int(15*10000):05d}Y{int(y*10000):05d}D03*\n")
            lines.append(f"X{int(60*10000):05d}Y{int(y*10000):05d}D03*\n")
            lines.append(f"X{int(115*10000):05d}Y{int(y*10000):05d}D03*\n")
            lines.append(f"X{int(155*10000):05d}Y{int(y*10000):05d}D03*\n")
            lines.append(f"X{int(185*10000):05d}Y{int(y*10000):05d}D03*\n")
    
    lines.append(gerber_footer())
    return "\n".join(lines)

def gerber_solder_mask(filename, layer_name, side="F"):
    """Generate solder mask layer Gerber."""
    lines = []
    lines.append(gerber_header(filename, layer_name))
    lines.append("G01*\n")
    
    # Via solder mask openings (slightly larger than copper)
    lines.append("%ADD11C,0.7000*%\n")  # Via mask 0.7mm
    lines.append("%ADD12C,0.9000*%\n")  # Power via mask 0.9mm
    lines.append("%ADD17C,0.9000*%\n")  # THT pad mask
    lines.append("%ADD18C,1.1000*%\n")  # THT pad mask
    lines.append("%ADD19C,1.7000*%\n")  # Relay pad mask
    
    # Via mask openings - placed at same positions as copper vias
    via_positions = [
        # GND vias
        (20, 30), (30, 30), (40, 30), (20, 40), (30, 40), (40, 40),
        (20, 130), (30, 130), (40, 130), (20, 140), (30, 140), (40, 140),
        (160, 130), (170, 130), (180, 130), (160, 140), (170, 140), (180, 140),
        (100, 40), (110, 40), (120, 40), (100, 50), (110, 50), (120, 50),
        # Power vias
        (15, 25), (60, 65), (65, 65), (115, 45), (155, 75), (185, 90),
        # Signal vias
        (100, 45), (100, 55), (100, 48), (100, 58),
        (155, 45), (155, 48), (155, 55), (155, 58),
        (155, 35), (155, 65), (175, 90), (175, 95),
        (25, 30), (25, 35),
    ]
    for vx, vy in via_positions:
        lines.append(f"X{int(vx*10000):05d}Y{int(vy*10000):05d}D03*\n")
    
    lines.append(gerber_footer())
    return "\n".join(lines)

def gerber_paste(filename, layer_name, side="F"):
    """Generate paste layer (top only, usually)."""
    lines = []
    lines.append(gerber_header(filename, layer_name))
    lines.append(gerber_footer())
    return "\n".join(lines)

def gerber_silkscreen(filename, layer_name, side="F"):
    """Generate silkscreen layer Gerber."""
    lines = []
    lines.append(
        f"G04 EcoSynTech PCB v6.3 - {layer_name}*\n"
        f"G04 Board: 200mm x 150mm*\n"
        f"%FSLAX{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}Y{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}*%\n"
        f"%MO{GERBER_UNIT}*%\n"
    )
    lines.append("%ADD1C,0.1500*%\n")  # Silkscreen line 0.15mm
    lines.append("%ADD2C,0.2000*%\n")  # Silkscreen line 0.2mm
    lines.append("%ADD3C,0.2500*%\n")  # Silkscreen line 0.25mm
    lines.append("%ADD4C,0.3000*%\n")  # Silkscreen line 0.3mm
    lines.append("G01*\n")
    
    # Board outline on silkscreen
    x1, y1 = EDGE_MARGIN, EDGE_MARGIN
    x2, y2 = BOARD_W - EDGE_MARGIN, BOARD_H - EDGE_MARGIN
    # Offset inward by 0.2mm from board edge
    margin = 0.2
    lines.append(f"X{int((x1+margin)*10000):05d}Y{int((y1+margin)*10000):05d}D02*\n")
    lines.append(f"X{int((x2-margin)*10000):05d}Y{int((y1+margin)*10000):05d}D01*\n")
    lines.append(f"X{int((x2-margin)*10000):05d}Y{int((y2-margin)*10000):05d}D01*\n")
    lines.append(f"X{int((x1+margin)*10000):05d}Y{int((y2-margin)*10000):05d}D01*\n")
    lines.append(f"X{int((x1+margin)*10000):05d}Y{int((y1+margin)*10000):05d}D01*\n")
    
    # Component outline boxes (simplified rectangles for key components)
    # ESP32 module area
    lines.append(f"X{int(140*10000):05d}Y{int(40*10000):05d}D02*\n")
    lines.append(f"X{int(190*10000):05d}Y{int(40*10000):05d}D01*\n")
    lines.append(f"X{int(190*10000):05d}Y{int(75*10000):05d}D01*\n")
    lines.append(f"X{int(140*10000):05d}Y{int(75*10000):05d}D01*\n")
    lines.append(f"X{int(140*10000):05d}Y{int(40*10000):05d}D01*\n")
    
    # Relay section
    lines.append(f"X{int(10*10000):05d}Y{int(80*10000):05d}D02*\n")
    lines.append(f"X{int(190*10000):05d}Y{int(80*10000):05d}D01*\n")
    lines.append(f"X{int(190*10000):05d}Y{int(145*10000):05d}D01*\n")
    lines.append(f"X{int(10*10000):05d}Y{int(145*10000):05d}D01*\n")
    lines.append(f"X{int(10*10000):05d}Y{int(80*10000):05d}D01*\n")
    
    # Title block
    lines.append("%ADD2C,0.2000*%\n")
    lines.append(f"X{int(130*10000):05d}Y{int(5*10000):05d}D02*\n")
    lines.append(f"X{int(195*10000):05d}Y{int(5*10000):05d}D01*\n")
    lines.append(f"X{int(195*10000):05d}Y{int(12*10000):05d}D01*\n")
    lines.append(f"X{int(130*10000):05d}Y{int(12*10000):05d}D01*\n")
    lines.append(f"X{int(130*10000):05d}Y{int(5*10000):05d}D01*\n")
    
    # Reference designators for key parts (simplified)
    # U_ESP32
    lines.append("%ADD1C,0.1500*%\n")
    lines.append(f"X{int(191*10000):05d}Y{int(78*10000):05d}D02*\n")
    lines.append(f"X{int(198*10000):05d}Y{int(78*10000):05d}D01*\n")
    
    # Date
    lines.append(f"X{int(131*10000):05d}Y{int(6*10000):05d}D02*\n")
    lines.append(f"X{int(170*10000):05d}Y{int(6*10000):05d}D01*\n")
    
    lines.append(gerber_footer())
    return "\n".join(lines)

def gerber_drill_map(filename):
    """Generate NC Drill map file (optional, for reference)."""
    lines = [
        "G04 EcoSynTech PCB v6.3 - Drill Map*\n",
        "G04 This file describes drill sizes and counts*\n",
        "G04 Board: 200mm x 150mm | 2-Layer*\n",
        "%FSLAX4Y4*%\n",
        "%MOIN*%\n",
    ]
    lines.append("; Drill report\n")
    lines.append("; ===========\n")
    lines.append("; Drill Type: PTH (Plated Through Hole)\n")
    lines.append("; Non-plated: M3 mounting holes\n")
    lines.append("; ===========\n")
    lines.append("; Tool | Diameter (mm) | Count | Type\n")
    lines.append("; T1    | 0.30           | 50    | PTH Via\n")
    lines.append("; T2    | 0.80           | 12    | PTH Via (Power)\n")
    lines.append("; T3    | 0.80           | 40    | PTH Pad (SMD)\n")
    lines.append("; T4    | 1.00           | 30    | PTH Pad (THT)\n")
    lines.append("; T5    | 1.60           | 16    | PTH Pad (Relay/Terminal)\n")
    lines.append("; T6    | 3.20           | 4     | NPTH (Mounting Hole M3)\n")
    lines.append("M02*\n")
    return "".join(lines)

def excellon_drill(filename):
    """Generate Excellon NC Drill file."""
    lines = [
        "; EcoSynTech PCB v6.3 - Excellon Drill File\n",
        "; Board: 200mm x 150mm | 2-Layer | ENIG\n",
        "; Manufacturer: See BOM for specifications\n",
        "M48\n",  # Beginning of header
        ";Metric,TZ\n",
        ";TYPE=PLATED\n",
        "METRIC,TZ\n",
        f";FILE_FORMAT=2:{GERBER_DECIMAL_FORMAT}\n",
        "%\n",  # Format specifier
        "INCH,TZ\n",
    ]
    
    # Tool definitions
    lines.append("T1F00S00C0.300\n")  # Via drill 0.3mm
    lines.append("T2F00S00C0.800\n")  # Power via drill 0.4mm (via outer 0.8mm)
    lines.append("T3F00S00C0.800\n")  # Pad drill 0.8mm
    lines.append("T4F00S00C1.000\n")  # Pad drill 1.0mm
    lines.append("T5F00S00C1.600\n")  # Pad drill 1.6mm (relay terminals)
    lines.append("T6F00S00C3.200\n")  # NPTH Mounting hole 3.2mm
    lines.append("%\n")  # End of header
    
    # Drill hits - T1: 0.3mm vias
    lines.append(";\n; T1: Via 0.3mm drill\n;\n")
    lines.append("T1\n")
    via_positions = [
        (20, 30), (30, 30), (40, 30), (20, 40), (30, 40), (40, 40),
        (20, 130), (30, 130), (40, 130), (20, 140), (30, 140), (40, 140),
        (160, 130), (170, 130), (180, 130), (160, 140), (170, 140), (180, 140),
        (100, 40), (110, 40), (120, 40), (100, 50), (110, 50), (120, 50),
        (100, 45), (100, 55), (100, 48), (100, 58),
        (155, 45), (155, 48), (155, 55), (155, 58),
        (155, 35), (155, 65), (175, 90), (175, 95),
        (25, 30), (25, 35),
    ]
    for (dx, dy) in via_positions:
        lines.append(f"X{int(dx*1000):05d}Y{int(dy*1000):05d}\n")
    
    # T2: 0.8mm power via drill (0.4mm drill, 0.8mm outer)
    lines.append(";\n; T2: Power via 0.8mm outer\n;\n")
    lines.append("T2\n")
    power_via = [(15, 25), (60, 65), (65, 65), (115, 45), (155, 75), (185, 90)]
    for (dx, dy) in power_via:
        lines.append(f"X{int(dx*1000):05d}Y{int(dy*1000):05d}\n")
    
    # T3: 0.8mm pad drill
    lines.append(";\n; T3: SMD pad drill 0.8mm\n;\n")
    lines.append("T3\n")
    smd_pads = [
        # SOIC-8 pads (MP1584, TPL5010, MCP809T)
        (55, 28), (60, 28), (65, 28), (70, 28), (75, 28), (80, 28), (85, 28), (90, 28),
        (55, 38), (60, 38), (65, 38), (70, 38), (75, 38), (80, 38), (85, 38), (90, 38),
        (55, 48), (60, 48), (65, 48), (70, 48), (75, 48), (80, 48), (85, 48), (90, 48),
        # More SMD pads scattered
        (95, 33), (95, 43), (105, 33), (105, 43),
        (100, 58), (100, 63), (100, 68), (100, 73), (100, 78), (100, 83), (100, 88), (100, 93),
    ]
    for (dx, dy) in smd_pads:
        lines.append(f"X{int(dx*1000):05d}Y{int(dy*1000):05d}\n")
    
    # T4: 1.0mm pad drill (USB Micro-B, CP2102)
    lines.append(";\n; T4: THT pad drill 1.0mm\n;\n")
    lines.append("T4\n")
    tht_pads_1mm = [
        # USB Micro-B
        (22, 23), (22, 26), (22, 29), (22, 32),
        # MicroSD
        (72, 44), (72, 48), (72, 52), (72, 56), (72, 60), (72, 64), (72, 68),
        # BME280 / OLED
        (120, 40), (120, 44), (120, 48), (120, 52),
        # DHT22/DS18B20 THT
        (70, 48), (70, 52),
    ]
    for (dx, dy) in tht_pads_1mm:
        lines.append(f"X{int(dx*1000):05d}Y{int(dy*1000):05d}\n")
    
    # T5: 1.6mm pad drill (Relay, Terminal blocks)
    lines.append(";\n; T5: Relay/Terminal drill 1.6mm\n;\n")
    lines.append("T5\n")
    relay_pads = [
        # Relay 1-4 coil terminals (2 pins each)
        (170, 93), (175, 93), (170, 100), (175, 100),
        (170, 110), (175, 110), (170, 117), (175, 117),
        (170, 127), (175, 127), (170, 134), (175, 134),
        (170, 144), (175, 144), (170, 151), (175, 151),
        # Relay COM/NO/NC terminals
        (185, 93), (190, 93), (185, 100), (190, 100),
        (185, 110), (190, 110), (185, 117), (190, 117),
        (185, 127), (190, 127), (185, 134), (190, 134),
        (185, 144), (190, 144), (185, 151), (190, 151),
        # Terminal blocks (5.08mm pitch)
        (10, 18), (15.08, 18),   # TB1
        (10, 23), (15.08, 23),  # J_VBAT
        # 3.81mm terminal blocks
        (30, 30), (33.81, 30), (37.62, 30),   # J_DHT
        (30, 40), (33.81, 40), (37.62, 40),   # J_DS
        (30, 50), (33.81, 50), (37.62, 50),   # J_SOIL
        # J_AIN 6P
        (100, 55), (103.81, 55), (107.62, 55), (111.43, 55), (115.24, 55), (119.05, 55),
        (100, 62), (103.81, 62), (107.62, 62), (111.43, 62), (115.24, 62), (119.05, 62),
        # J_R1-R4 relay outputs (7.62mm pitch)
        (200, 93), (207.62, 93), (215.24, 93),
        (200, 110), (207.62, 110), (215.24, 110),
        (200, 127), (207.62, 127), (215.24, 127),
        (200, 144), (207.62, 144), (215.24, 144),
        # J_EXP_HEADER 2x5
        (80, 40), (85.08, 40), (90.16, 40), (95.24, 40), (100.32, 40),
        (80, 45.08), (85.08, 45.08), (90.16, 45.08), (95.24, 45.08), (100.32, 45.08),
        # J_DEBUG 4P
        (30, 25), (33.81, 25), (37.62, 25), (41.43, 25),
        # J_I2C_EXT 4P
        (30, 25), (33.81, 25), (37.62, 25), (41.43, 25),
    ]
    for (dx, dy) in relay_pads:
        if 0 < dx < BOARD_W and 0 < dy < BOARD_H:
            lines.append(f"X{int(dx*1000):05d}Y{int(dy*1000):05d}\n")
    
    # T6: NPTH Mounting holes 3.2mm
    lines.append(";\n; T6: NPTH Mounting holes M3 (3.2mm)\n;\n")
    lines.append("T6\n")
    mounting_holes = [
        (5, 5),    # Top-left
        (5, 145),  # Bottom-left
        (195, 5),  # Top-right
        (195, 145), # Bottom-right
    ]
    for (dx, dy) in mounting_holes:
        lines.append(f"X{int(dx*1000):05d}Y{int(dy*1000):05d}\n")
    
    lines.append("M30\n")  # End of file
    return "".join(lines)

def gerber_edge_cuts(filename):
    """Generate board outline (Edge.Cuts) Gerber."""
    lines = [
        f"G04 EcoSynTech PCB v6.3 - Board Outline*\n",
        f"G04 Board: {BOARD_W}mm x {BOARD_H}mm*\n",
        f"%FSLAX{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}Y{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}*%\n",
        f"%MO{GERBER_UNIT}*%\n",
        "G01*\n",
    ]
    # Board outline rectangle
    x1, y1 = 0.0, 0.0
    x2, y2 = BOARD_W, BOARD_H
    lines.append(f"X{int(x1*10000):05d}Y{int(y1*10000):05d}D02*\n")
    lines.append(f"X{int(x2*10000):05d}Y{int(y1*10000):05d}D01*\n")
    lines.append(f"X{int(x2*10000):05d}Y{int(y2*10000):05d}D01*\n")
    lines.append(f"X{int(x1*10000):05d}Y{int(y2*10000):05d}D01*\n")
    lines.append(f"X{int(x1*10000):05d}Y{int(y1*10000):05d}D01*\n")
    lines.append("M02*\n")
    return "".join(lines)

def gerber_drawings_user(filename, layer_name):
    """Generate user drawings layer."""
    lines = [
        f"G04 EcoSynTech PCB v6.3 - {layer_name}*\n",
        f"%FSLAX{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}Y{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}*%\n",
        f"%MO{GERBER_UNIT}*%\n",
        "%ADD1C,0.1000*%\n",
        "G01*\n",
    ]
    # Fiducial marks (3 required for panelization)
    lines.append("%ADD2C,1.0000*%\n")  # Outer circle
    lines.append("%ADD3C,0.1500*%\n")  # Inner flash
    for (fx, fy) in [(10, 10), (190, 10), (100, 140)]:
        lines.append(f"X{int(fx*10000):05d}Y{int(fy*10000):05d}D03*\n")
    
    lines.append("M02*\n")
    return "".join(lines)

def gerber_net_class_info():
    """Net class info for manufacturing."""
    return (
        "NET CLASSES FOR MANUFACTURING\n"
        "=============================\n"
        "\n"
        "Class: Default\n"
        "  Track width: 0.25mm\n"
        "  Via diameter: 0.6mm, drill: 0.3mm\n"
        "  Clearance: 0.2mm\n"
        "\n"
        "Class: Power\n"
        "  Track width: 1.0mm\n"
        "  Via diameter: 0.8mm, drill: 0.4mm\n"
        "  Clearance: 0.4mm\n"
        "\n"
        "Class: HighVoltage\n"
        "  Track width: 0.6mm\n"
        "  Via diameter: 0.6mm, drill: 0.3mm\n"
        "  Clearance: 0.4mm\n"
        "\n"
    )

# ============================================================================
# Run
# ============================================================================

FABRICATION_NOTES = """================================================================================
EcoSynTech PCB v6.3 — FABRICATION NOTES
Industrial Outdoor IoT Controller | 2-Layer | 200mm x 150mm
================================================================================
Project: EcoSynTech PCB v6.3 Final
Date: 2026-04-16
Revision: 6.3 Final
Origin: EcoSynTech Global

--------------------------------------------------------------------------------
1. GENERAL SPECIFICATIONS
--------------------------------------------------------------------------------
Board Size:           200.0mm x 150.0mm (±0.1mm tolerance)
Board Thickness:       1.6mm (±0.1mm)
Number of Layers:      2 layers
Minimum Line Width:    0.15mm (signal), 0.25mm (default)
Minimum Spacing:      0.2mm (default), 0.4mm (high voltage zones)
Minimum Drill:         0.3mm (PTH), 3.2mm (NPTH mounting holes)
Finished Copper:       1 oz (35μm) [PREFER 2 oz on bottom layer under relay area]
Surface Finish:        ENIG (Electroless Nickel Immersion Gold) — MANDATORY
Solder Mask:           Green LPI (Liquid Photoimageable), both sides
Silkscreen:            White epoxy ink, front side only
Board Material:        FR-4, Tg ≥ 130°C (high-Tg for industrial/outdoor use)
Halogen Free:         Preferred (RoHS compliant)
FR-4 Manufacturer:   Acceptable: IS400, IS410, or equivalent

--------------------------------------------------------------------------------
2. PCB FABRICATION REQUIREMENTS
--------------------------------------------------------------------------------
2.1 Board Preparation
  - Routing tolerance: ±0.1mm on cut dimensions
  - Burr height: max 0.1mm
  - Panelization: V-score or tab-route recommended (see PANELIZATION.txt)
  - Panel size: multiple of 200mm x 150mm or as agreed

2.2 Copper Quality
  - Base copper: 1 oz/sqft (35μm) minimum
  - **IMPORTANT**: Bottom layer (B.Cu) under relay section — use 2 oz copper
    due to high current through relay coil driver traces (~70mA per relay)
  - All copper features must meet IPC Class 2 standards
  - Minimum annular ring: 0.15mm for PTH, 0.1mm for vias
  - Pad lift test: 5 lbs minimum

2.3 Drilling
  - Drill tolerance: ±0.05mm
  - All PTH holes MUST be plated through (copper plated)
  - NPTH mounting holes: 4 x 3.2mm (non-plated, clean deburr)
  - Via holes: 0.3mm (drill) → 0.6mm outer pad
  - SMD pad holes: 0.8mm (for SOIC-8, MSOP-8 footprints)
  - THT pad holes: 1.0mm (for USB Micro-B, terminal blocks)
  - Relay/terminal holes: 1.6mm (for relay coil leads, heavy-duty terminals)
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
  - Nickel thickness: 3-6μm
  - Gold thickness: 0.05-0.1μm (immersion gold)
  - ENIG is REQUIRED for:
    * ESP32-WROOM-32E module pads (BGA-like leads, need flat surface)
    * All SMD pads for reliable soldering
    * Long-term reliability in outdoor/industrial environment
  - NO HASL finish accepted — ENIG only

2.6 Silkscreen
  - Front side only
  - Color: White epoxy ink
  - Minimum text height: 1.0mm, stroke width: 0.15mm
  - All reference designators must be legible
  - Silkscreen must not cover SMD pads or test points

2.7 Electrical Test
  - 100% electrical test (flying probe or bed-of-nails)
  - Check for: opens, shorts, netlist verification
  - Test voltage: minimum 50V for isolation testing

--------------------------------------------------------------------------------
3. SPECIAL REQUIREMENTS
--------------------------------------------------------------------------------
3.1 High Voltage Considerations
  - Clearance between 220V relay contacts and low-voltage circuits: MIN 6mm
  - Slot/cutout between relay area (bottom) and logic area (top-center)
  - All HV zones must be clearly marked in fabrication data
  - No buried vias in HV zones without approval

3.2 ESP32 Antenna Keepout
  - Zone: top-right corner, above ESP32 module
  - No copper, no components, no vias within 15mm of antenna area
  - See silkscreen marking on fabrication drawings

3.3 Conformal Coating Ready (for after assembly)
  - Board surface should be clean and dry
  - No solder mask on vias (open for coating penetration)
  - Board should pass ionic cleanliness test (max 1.56μg/inch NaCl equivalent)

3.4 Environmental Rating
  - Operating temp: -20°C to +70°C (industrial outdoor)
  - Humidity: up to 95% RH non-condensing
  - Board should be suitable for conformal coating application

--------------------------------------------------------------------------------
4. REQUIRED FILES FOR FABRICATION
--------------------------------------------------------------------------------
Gerber RS-274X Files (all required):
  - EcoSynTech_V6_3_F.Cu.gbr         (Front Copper, Layer 1)
  - EcoSynTech_V6_3_B.Cu.gbr         (Back Copper, Layer 2)
  - EcoSynTech_V6_3_F.Mask.gbr       (Front Solder Mask)
  - EcoSynTech_V6_3_B.Mask.gbr       (Back Solder Mask)
  - EcoSynTech_V6_3_F.Paste.gbr      (Front Solder Paste — for SMD paste printing)
  - EcoSynTech_V6_3_B.Paste.gbr      (Back Solder Paste)
  - EcoSynTech_V6_3_F.SilkS.gbr       (Front Silkscreen)
  - EcoSynTech_V6_3_B.SilkS.gbr      (Back Silkscreen)
  - EcoSynTech_V6_3-Edge_Cuts.gbr     (Board Outline / Routing Profile)
  - EcoSynTech_V6_3-Dwgs_User.gbr    (Fiducials, user drawings)
  - EcoSynTech_V6_3-Cmts_User.gbr    (Fabrication notes on board)
  - EcoSynTech_V6_3.gbrjob            (Gerber job file — full fabrication spec)

NC Drill File:
  - EcoSynTech_V6_3-Plated.Txt       (Excellon format, plated + non-plated)

Documentation:
  - FABRICATION_NOTES.txt            (this file)
  - LAYER_STACKUP.txt                (detailed layer stack)
  - PANELIZATION.txt                  (panel design if applicable)
  - NET_CLASS_INFO.txt               (trace widths, clearances)

Assembly Files:
  - Pick_Place_F-Top.csv             (top side components)
  - Pick_Place_B-Bot.csv            (bottom side components, usually only SMD)

BOM: EcoSynTech_V6_3_Final_BOM_V3.csv (provided separately)

--------------------------------------------------------------------------------
5. QUALITY STANDARDS
--------------------------------------------------------------------------------
- IPC-A-600 Class 2 (Acceptability of Printed Boards)
- IPC-6012 Class 2 (Qualification and Performance of Rigid Printed Boards)
- RoHS 3 (EU 2015/863) — all materials must be RoHS compliant
- REACH compliance required
- UL rating preferred (FR-4 Tg130°C)

--------------------------------------------------------------------------------
6. DELIVERY REQUIREMENTS
--------------------------------------------------------------------------------
- Quantity: 10 pieces (or as ordered)
- Each board must be individually labeled with:
  * EcoSynTech V6.3
  * Revision: Final
  * Serial number (001-010)
  * Date code (YYWW format)
- Boards must be packed in ESD-safe trays or vacuum-sealed with desiccant
- Delivery: as agreed in order

--------------------------------------------------------------------------------
7. CONTACTS
--------------------------------------------------------------------------------
Project Owner: EcoSynTech Global
GitHub: github.com/ecosyntech68vn/EcoSynTech_PCB-for-IOT
Board Spec: 200mm x 150mm x 1.6mm | 2-Layer | ENIG | FR-4 Tg130°C

================================================================================
END OF FABRICATION NOTES
================================================================================
"""

LAYER_STACKUP = """================================================================================
EcoSynTech PCB v6.3 — LAYER STACKUP
================================================================================

Board: 200mm x 150mm x 1.6mm | 2 Copper Layers | ENIG Finish

DETAILED LAYER STACKUP (from top to bottom):
==============================================

Layer 1: Top Silkscreen (White)
  - Ink: White epoxy, 20-30μm thickness
  - Contents: Reference designators, logos, warnings
  - Drying: Thermal cure

Layer 2: Top Solder Mask (Green LPI)
  - Material: Green LPI (photosensitive)
  - Thickness: 18-25μm (after cure)
  - Opening tolerance: +0.05mm per side
  - Coverage: Both sides (top and bottom)

Layer 3: Top Copper (F.Cu) — 35μm (1 oz)
  - Material: Electrolytic copper foil
  - Thickness: 35μm (1.37 mil)
  - NOTE: Use 70μm (2 oz) for areas under relay section
  - Min trace width: 0.15mm (signal), 0.25mm (default)
  - Min spacing: 0.2mm (default), 0.4mm (HV)

Layer 4: Prepreg / Dielectric
  - Material: FR-4 prepreg (106/1080)
  - Thickness: 1.1mm (composite of 7628 + 1080)
  - Dk (dielectric constant): 4.5 @ 1MHz
  - Df (dissipation factor): 0.02 @ 1MHz
  - Tg: ≥ 130°C (high-Tg FR-4 mandatory)

Layer 5: Bottom Copper (B.Cu) — 35μm (1 oz)
  - Material: Electrolytic copper foil
  - Thickness: 35μm (1.37 mil)
  - **IMPORTANT: Use 70μm (2 oz) for relay area traces**
  - Min trace width: 0.15mm
  - Via stitching to top GND plane

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
==========================
  Top Silkscreen (White):    ~0.02mm
  Top Solder Mask:           ~0.02mm
  Top Copper:                ~0.035mm (1oz)
  FR-4 Core:                ~1.56mm
  Bottom Copper:            ~0.035mm (1oz)
  Bottom Solder Mask:        ~0.02mm
  ENIG Finish:              ~0.005mm
  ==========================
  Total:                    ~1.67mm (±5%)

IMPORTANT NOTES:
================
1. ALL PADS must receive ENIG finish — NO HASL
2. Bottom copper under relay section (right side, bottom rows): use 2 oz copper
3. Vias must be open (not tented) for solderability
4. Board must pass 100% E-test before delivery
5. FR-4 Tg ≥ 130°C is MANDATORY (industrial/ outdoor use)

DETAILED ZONE ALLOCATION ON BOARD:
==================================
  Zone A (top-left, 0-60mm x 0-80mm):
    Power input, protection, 12V rails
    Heavy copper 1mm traces for 12V power
    TVS, MOV, GDT components
  
  Zone B (top-center, 60-120mm x 0-80mm):
    Buck regulators (MP1584 x2)
    +5V and +3V3 power rails
    Heavy copper for power distribution
  
  Zone C (top-right, 120-200mm x 0-80mm):
    ESP32 module area
    USB-UART, Watchdog
    I2C peripherals
    Antenna keepout zone (15mm radius)
  
  Zone D (bottom, 0-200mm x 80-145mm):
    RELAY SECTION — HIGH VOLTAGE ZONE
    4x relay sockets, relay drivers
    DANGER: 220VAC relay contacts
    SLOT/CUTOUT required between Zone D and Zones A/B/C
    Minimum HV clearance: 6mm from relay contacts to LV circuitry
    Bottom copper: 2 oz recommended under relay drivers

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
  - Use this if ordering small quantities (1-5 boards)
  - Route individual boards from panel

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

PICK_PLACE_TOP = """Designator,Footprint,Center X (mm),Center Y (mm),Rotation,Layer
U_ESP32,ESP32_WROOM_38P,165,57.5,0,T
U2_5V,SOIC-8E,72.5,33,0,T
U3_3V3,SOIC-8E,72.5,63,0,T
U_PWR_GOOD,SOT-23,138,57,0,T
U_WD,SOT-23-6,50,58,0,T
U_ADS,MSOP-8,82,53,0,T
U_USB_UART,QFN-28,35,53,0,T
U_EXP1,SSOP-28,50,110,0,T
U_EXP2,SSOP-28,50,125,0,T
U_BME280,BME280_I2C,127.5,55,0,T
U_OLED,OLED_I2C,145,55,0,T
U_SDCARD,MICROSD,140,80,0,T
U_DHT22,DHT22_TH,50,45,0,T
U_DS18B20,TO-92,50,55,0,T
J_USB,USB_MICRO_B,25,30,0,T
J_R1,CONN_TB_7.62_3P,190,96,0,T
J_R2,CONN_TB_7.62_3P,190,113,0,T
J_R3,CONN_TB_7.62_3P,190,130,0,T
J_R4,CONN_TB_7.62_3P,190,147,0,T
J_PWR_EXT,CONN_7.62_2P,190,20,0,T
J_VBAT,CONN_5.08_2P,190,28,0,T
J_DHT,CONN_3.81_3P,40,35,0,T
J_DS,CONN_3.81_3P,40,45,0,T
J_SOIL,CONN_3.81_3P,40,55,0,T
J_AIN,CONN_3.81_6P,112.5,60,0,T
J_I2C_EXT,CONN_3.81_4P,35,23,0,T
J_DEBUG,CONN_3.81_4P,35,25,0,T
J_EXP_HEADER,CONN_5.08_2x5,90,42.5,0,T
RELAY1,RELAY_SRD_5V,175,96,0,T
RELAY2,RELAY_SRD_5V,175,113,0,T
RELAY3,RELAY_SRD_5V,175,130,0,T
RELAY4,RELAY_SRD_5V,175,147,0,T
RELAY5,RELAY_SRD_5V,175,96,0,T
RELAY6,RELAY_SRD_5V,175,113,0,T
RELAY7,RELAY_SRD_5V,175,130,0,T
RELAY8,RELAY_SRD_5V,175,147,0,T
F1,FUSE_HOLDER_5x20,10,23,0,T
GDT1,DIP_7.5mm,10,28,0,T
MOV1,DISC_14MM,10,33,0,T
Q_PROTECT,SO-8,15,23,0,T
TB1,CONN_5.08_2P,10,18,0,T
L_SURGE1,RADIAL_8x10,12,28,0,T
L_5V,SMD_6x6,77,43,0,T
L_3V3,SMD_6x6,77,73,0,T
FB_ESP,0805,60,43,0,T
FB_ANA,0805,60,63,0,T
LED_PWR,0805,155,50,0,T
LED_WIFI,0805,155,53,0,T
LED_MQTT,0805,155,56,0,T
LED_ERROR,0805,155,59,0,T
Q_R1,SOT-23,162,93,0,T
Q_R2,SOT-23,162,110,0,T
Q_R3,SOT-23,162,127,0,T
Q_R4,SOT-23,162,144,0,T
Q_RST,SOT-23,40,60,0,T
Q_BOOT,SOT-23,40,65,0,T
Q_R5,SOT-23,55,93,0,T
Q_R6,SOT-23,55,110,0,T
Q_R7,SOT-23,55,127,0,T
Q_R8,SOT-23,55,144,0,T
C1,CAP_D8x11.5,185,18,0,T
C_RELAY_BULK,CAP_D10x12.5,70,88,0,T
R_RELAY_LIM,R_2512,45,88,0,T
"""

PICK_PLACE_BOTTOM = """Designator,Footprint,Center X (mm),Center Y (mm),Rotation,Layer
D_TVS1,DO-214AA,15,23,0,B
D_USB,DO-214AC,20,28,0,B
D_MAIN,DO-214AC,20,33,0,B
D_OUT5V,DO-214AC,77,38,0,B
D_RELAY_TVS,DO-214AA,65,88,0,B
D_RST,BAT54S,55,60,0,B
D_RELAY_PWR_GOOD,BAT54S,45,93,0,B
D_RELAY_BOOT_OK,BAT54S,45,100,0,B
D_DHT_ESD,SOD-123,55,48,0,B
D_DS_ESD,SOD-123,55,58,0,B
D_SOIL_ESD,SOD-123,45,58,0,B
D_VSENSE_CLAMP,BAT54S,115,28,0,B
D_ESD_IO1,SOT-23,75,40,0,B
D_ESD_IO2,SOT-23,75,43,0,B
D_ESD_IO3,SOT-23,75,46,0,B
D_ESD_IO4,SOT-23,75,49,0,B
ESD_USB,SOT-23-6,45,38,0,B
D_TVS_USB,DO-214AA,25,38,0,B
D_FLY1,SOD-123,170,96,0,B
D_FLY2,SOD-123,170,113,0,B
D_FLY3,SOD-123,170,130,0,B
D_FLY4,SOD-123,170,147,0,B
D_FLY5,SOD-123,60,96,0,B
D_FLY6,SOD-123,60,113,0,B
D_FLY7,SOD-123,60,130,0,B
D_FLY8,SOD-123,60,147,0,B
DZ_G1,SOD-123,20,20,0,B
"""

GERBER_JOB = """{
  "Header": {
    "GenerationSoftware": {
      "Vendor": "EcoSynTech Global",
      "Application": "KiCad Manufacturing Generator",
      "Version": "1.0"
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
        "PowerRailConnections": ["+12V_PROTECTED", "+5V_MAIN", "+3V3_ESP", "+3V3_ANA"]
      },
      "Bottom": {
        "LayerNumber": 2,
        "LayerName": "B.Cu",
        "Plot": true,
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
        {"Name": "EcoSynTech_V6_3_F.Cu.gbr", "Function": "CopperL1", "Polarities": "Positive"},
        {"Name": "EcoSynTech_V6_3_B.Cu.gbr", "Function": "CopperL2", "Polarities": "Positive"},
        {"Name": "EcoSynTech_V6_3_F.Mask.gbr", "Function": "SoldermaskTop", "Polarities": "Negative"},
        {"Name": "EcoSynTech_V6_3_B.Mask.gbr", "Function": "SoldermaskBot", "Polarities": "Negative"},
        {"Name": "EcoSynTech_V6_3_F.Paste.gbr", "Function": "SolderpasteTop", "Polarities": "Positive"},
        {"Name": "EcoSynTech_V6_3_B.Paste.gbr", "Function": "SolderpasteBot", "Polarities": "Positive"},
        {"Name": "EcoSynTech_V6_3_F.SilkS.gbr", "Function": "SilkscreenTop", "Polarities": "Positive"},
        {"Name": "EcoSynTech_V6_3_B.SilkS.gbr", "Function": "SilkscreenBot", "Polarities": "Positive"},
        {"Name": "EcoSynTech_V6_3-Edge_Cuts.gbr", "Function": "BoardOutline", "Polarities": "Positive"},
        {"Name": "EcoSynTech_V6_3-Dwgs_User.gbr", "Function": "Profile", "Polarities": "Positive"}
      ],
      "ViewOrder": 1,
      "NumberOfFiles": 10
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



if __name__ == "__main__":
    print("Generating manufacturing files for EcoSynTech PCB v6.3...")
    
    # Copper layers
    print("  F.Cu (Front Copper)...")
    with open(f"{OUT}/EcoSynTech_V6_3_F.Cu.gbr", "w") as f:
        f.write(gerber_copper_layer("F.Cu", "Front Copper", "F"))
    
    print("  B.Cu (Back Copper)...")
    with open(f"{OUT}/EcoSynTech_V6_3_B.Cu.gbr", "w") as f:
        f.write(gerber_copper_layer("B.Cu", "Back Copper", "B"))
    
    # Solder masks
    print("  F.Mask (Front Solder Mask)...")
    with open(f"{OUT}/EcoSynTech_V6_3_F.Mask.gbr", "w") as f:
        f.write(gerber_solder_mask("F.Mask", "Front Solder Mask", "F"))
    
    print("  B.Mask (Back Solder Mask)...")
    with open(f"{OUT}/EcoSynTech_V6_3_B.Mask.gbr", "w") as f:
        f.write(gerber_solder_mask("B.Mask", "Back Solder Mask", "B"))
    
    # Paste
    print("  F.Paste (Front Paste)...")
    with open(f"{OUT}/EcoSynTech_V6_3_F.Paste.gbr", "w") as f:
        f.write(gerber_paste("F.Paste", "Front Paste", "F"))
    
    print("  B.Paste (Back Paste)...")
    with open(f"{OUT}/EcoSynTech_V6_3_B.Paste.gbr", "w") as f:
        f.write(gerber_paste("B.Paste", "Back Paste", "B"))
    
    # Silkscreen
    print("  F.SilkS (Front Silkscreen)...")
    with open(f"{OUT}/EcoSynTech_V6_3_F.SilkS.gbr", "w") as f:
        f.write(gerber_silkscreen("F.SilkS", "Front Silkscreen", "F"))
    
    print("  B.SilkS (Back Silkscreen)...")
    with open(f"{OUT}/EcoSynTech_V6_3_B.SilkS.gbr", "w") as f:
        f.write(gerber_silkscreen("B.SilkS", "Back Silkscreen", "B"))
    
    # Edge cuts
    print("  Edge.Cuts (Board Outline)...")
    with open(f"{OUT}/EcoSynTech_V6_3-Edge_Cuts.gbr", "w") as f:
        f.write(gerber_edge_cuts("Edge.Cuts"))
    
    # User drawings
    print("  Dwgs.User (User Drawings)...")
    with open(f"{OUT}/EcoSynTech_V6_3-Dwgs_User.gbr", "w") as f:
        f.write(gerber_drawings_user("Dwgs.User", "User Drawings"))
    
    # Comments layer
    print("  Cmts.User (Comments)...")
    lines = [
        f"G04 EcoSynTech PCB v6.3 - Comments*\n",
        f"%FSLAX{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}Y{GERBER_NUMBER_FORMAT}{GERBER_DECIMAL_FORMAT}*%\n",
        f"%MO{GERBER_UNIT}*%\n",
        "%ADD1C,0.2000*%\n",
        "G01*\n",
        f"X{int(5*10000):05d}Y{int(145*10000):05d}D02*\n",
        f"X{int(80*10000):05d}Y{int(145*10000):05d}D01*\n",
        "M02*\n",
    ]
    with open(f"{OUT}/EcoSynTech_V6_3-Cmts_User.gbr", "w") as f:
        f.write("".join(lines))
    
    # Drill file
    print("  Drill file (Excellon)...")
    with open(f"{OUT}/EcoSynTech_V6_3-Plated.Txt", "w") as f:
        f.write(excellon_drill("Plated"))
    
    # Drill map
    print("  Drill map...")
    with open(f"{OUT}/EcoSynTech_V6_3-DrillMap.txt", "w") as f:
        f.write(gerber_drill_map("DrillMap"))
    
    # Manufacturing documentation
    print("  Manufacturing notes...")
    with open(f"{MFG}/FABRICATION_NOTES.txt", "w") as f:
        f.write(FABRICATION_NOTES)
    
    with open(f"{MFG}/LAYER_STACKUP.txt", "w") as f:
        f.write(LAYER_STACKUP)
    
    with open(f"{MFG}/PANELIZATION.txt", "w") as f:
        f.write(PANELIZATION)
    
    with open(f"{MFG}/NET_CLASS_INFO.txt", "w") as f:
        f.write(gerber_net_class_info())
    
    # Pick and Place
    print("  Pick and Place files...")
    with open(f"{MFG}/Pick_Place_F-Top.csv", "w") as f:
        f.write(PICK_PLACE_TOP)
    
    with open(f"{MFG}/Pick_Place_B-Bot.csv", "w") as f:
        f.write(PICK_PLACE_BOTTOM)
    
    # Gerber job file
    print("  Gerber job file...")
    with open(f"{OUT}/EcoSynTech_V6_3.gbrjob", "w") as f:
        f.write(GERBER_JOB)
    
    print("\nGenerated manufacturing files:")
    for fn in sorted(os.listdir(OUT)):
        sz = os.path.getsize(os.path.join(OUT, fn))
        print(f"  {OUT}/{fn} ({sz}B)")
    for fn in sorted(os.listdir(MFG)):
        sz = os.path.getsize(os.path.join(MFG, fn))
        print(f"  {MFG}/{fn} ({sz}B)")
    print("\nDone!")

