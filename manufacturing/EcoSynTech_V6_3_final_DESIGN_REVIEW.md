# EcoSynTech PCB v6.3 Final — Design Review Report
# vs Original Docx Requirements
# Revision: V3 (Updated 2026-05-03 — reflects BOM_V3 and all V3 fixes)
# Original review date: 2026-04-15 | Update date: 2026-05-03
# ==============================================================

## CHANGELOG — V3 UPDATE (2026-05-03)
All 18 critical issues from the original review have been resolved in BOM_V3.
PC817 optocouplers added to BOM_V3. NPTH drill file generated.
Score updated from 6/10 → 8.5/10.

---

## SECTION 1: CRITICAL ISSUES — STATUS

### ✅ RESOLVED IN V3

| Issue | Fix Applied |
|---|---|
| LDO instead of 2nd buck | Replaced AMS1117 with MP1584 #2 (U3_3V3) |
| Wrong GPIO assignments | All GPIOs corrected per spec B7 |
| Wrong LED polarity (active-HIGH) | Fixed to active-LOW, R=1.5kΩ |
| Missing relay power limiting | R_RELAY_LIM (0.5Ω 1W) + C_RELAY_BULK (1000µF) added |
| Missing auto-reset circuit | Q_RST + Q_BOOT (BC847) added |
| Missing TVS on signal lines | SMBJ5.0A on DHT22/DS18B20/SOIL/ADS A0-A3/I2C |
| Missing BAT54S diodes | D_RST + D_VSENSE_CLAMP added |
| Missing OR-ing diodes +5V_SYS | D_USB + D_MAIN (SS34) added |
| Missing C_BST caps | C_BST_5V + C_BST_3V3 (100nF) added |
| Wrong I2C pull-up rail | Changed from +3V3_ESP to +3V3_ANA |
| Missing 22Ω series I2C/SD | R_I2C_SCL/SDA_SER + R_SD_* (22Ω) added |
| Missing 100Ω series DHT/DS | R_DHT_SER + R_DS_SER (100Ω) added |
| Wrong LED resistor 470Ω | Changed to 1.5kΩ all LED resistors |
| Missing relay bulk cap | C_RELAY_BULK 1000µF 16V 105°C added |
| Missing ferrite beads | FB_ESP + FB_ANA (BLM18PG121SN1) added |
| Missing POWER_GOOD supervisor | U_PWR_GOOD (MCP809T-315) added |
| Missing hardware interlock | D_RELAY_PWR_GOOD + D_RELAY_BOOT_OK (BAT54S) added |
| Surface finish HASL→ENIG | ENIG specified in FABRICATION_NOTES.txt |

### ✅ NEWLY ADDED IN V3

| Addition | Detail |
|---|---|
| PC817C optocouplers x4 | OC_R1–OC_R4 (DIP-4) — relay GPIO isolation |
| Opto LED resistors R_OC1–4 | 1kΩ — current limit from 3.3V GPIO |
| Opto collector pull-ups R_OC_PU1–4 | 10kΩ to +3V3_ESP → S8050 base |
| NPTH drill file | EcoSynTech_V6_3-NPTH.drl — 4× M3 3.2mm NPTH |

### ⚠️ REMAINING ACTION ITEMS

| Item | Action Required | Owner |
|---|---|---|
| PC817 schematic verify | Confirm OC_R1-4 footprints & nets in KiCad → push .kicad_sch | Designer |
| Gerber root cleanup | Delete duplicate .gbr files from root / — keep only /gerber/ | Designer |
| GitHub release tag | Create tag v6.3-release after final commit | Designer |

---

## SECTION 2: LAYOUT STATUS

| Issue | Status |
|---|---|
| Via stitching along relay isolation slot | ✅ Specified in FABRICATION_NOTES |
| Thermal vias under MP1584 | ⚠️ Verify in .kicad_pcb |
| 2 oz copper relay zone | ✅ Specified in FABRICATION_NOTES |
| 6-8mm relay isolation slot | ⚠️ Verify clearance in .kicad_pcb |
| Antenna keepout zone | ✅ Specified in FABRICATION_NOTES |
| All test points present | ✅ 16 test points in BOM_V3 |

---

## SECTION 3: BOM STATUS

| Category | Status |
|---|---|
| CSV format error | ✅ Fixed — all section headers normalized to 9 columns |
| PC817 optocouplers | ✅ Added OC_R1–OC_R4 + associated passives |
| All critical protection components | ✅ Present in BOM_V3 |
| Second source options | ✅ Documented (AP63205/CH340C/HF46F/TLP291) |
| LCSC part numbers | ✅ All populated |
| NPTH mounting holes note | ✅ J_MOUNT1 notes updated with drill file reference |

---

## SECTION 4: FABRICATION READINESS

| File | Status |
|---|---|
| Gerber set (F.Cu, B.Cu, Mask, Paste, Silk, Edge_Cuts) | ✅ Present in /gerber/ |
| PTH drill file | ✅ EcoSynTech_V6_3-Plated.Txt |
| NPTH drill file | ✅ EcoSynTech_V6_3-NPTH.drl (NEW) |
| Pick & Place Top/Bot | ✅ Pick_Place_F-Top.csv + B-Bot.csv |
| BOM | ✅ BOM_V3 (fixed) |
| Fabrication Notes | ✅ FABRICATION_NOTES.txt — ENIG + 2oz + flying probe |
| Layer stackup | ✅ LAYER_STACKUP.txt |
| Panelization | ✅ PANELIZATION.txt |

---

## SECTION 5: OVERALL VERDICT — UPDATED

### Score: 8.5/10 — Ready for prototype run after schematic PC817 verify

| Category | V1 Score | V3 Score | Notes |
|---|---|---|---|
| Power architecture | 5/10 | 10/10 | Dual buck + ferrite + OR-ing all correct |
| GPIO assignments | 2/10 | 10/10 | All corrected per spec B7 |
| Signal protection | 5/10 | 10/10 | TVS on all external lines |
| Relay driver circuit | 4/10 | 9/10 | PC817 added; verify in schematic |
| LED circuit | 2/10 | 10/10 | Active-LOW + 1.5kΩ |
| Auto-reset circuit | 0/10 | 10/10 | Q_RST + Q_BOOT added |
| Layout | 6/10 | 7/10 | Thermal vias + slot clearance to verify |
| Silkscreen | 3/10 | 8/10 | Labels in FABRICATION_NOTES |
| BOM | 5/10 | 10/10 | All components present, CSV fixed |
| DFM for outdoor | 6/10 | 9/10 | ENIG + conformal coating spec |
| Expandability | 8/10 | 9/10 | MCP23017 x2 expansion solid |
| Fab file completeness | 4/10 | 9/10 | NPTH drill added |
| **OVERALL** | **6/10** | **8.5/10** | |

### REMAINING ITEMS BEFORE FAB SUBMIT:
1. 🟡 VERIFY: Open KiCad → confirm PC817 in S09_Relay_Drivers.kicad_sch → push
2. 🟡 CLEANUP: Delete root-level .gbr files (keep /gerber/ only)
3. 🟢 TAG: `git tag v6.3-release && git push --tags`
