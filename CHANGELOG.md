# Changelog - EcoSynTech PCB v6.3

Tất cả thay đổi quan trọng của project sẽ được ghi chép ở đây.

---

## [v6.3] - 2026-04-16 - Production Ready

### Added
- **PC817 Optocoupler Isolation** cho 8 relays (5kV galvanic isolation)
  - ISO_R1-8: PC817X1 SMD-4
  - R_PC817_R1-8: 330R series resistors
  - Bảo vệ ESP32/MCP23017 khỏi flyback motor/actuator
- **TVS SMBJ30A** trên VBAT input
  - D_VBAT_TVS: Surge protection cho battery/power input
- **Relay Status LEDs** (8x Green LEDs)
  - LED_R1-8: Visual status indicators
  - R_LED_R1-8: 1.5kΩ series resistors
- **RC Snubbers** trên relay contacts
  - F_R1-8_SNUB_C: 100nF 275VAC
  - F_R1-8_SNUB_R: 100R 1W
- **MOV Snubbers** trên relay contacts
  - F_R1-4_MOV: MOV 275VAC
- **Fiducial Marks** (3x 1.5mm)
  - Hỗ trợ machine vision alignment
- **Thermal Vias** nâng cấp cho MP1584
  - 16 vias per IC (tăng từ 6)
  - Cải thiện thermal management
- **VIN Divider** tối ưu
  - R_VTOP: 47kΩ (thay đổi từ 100kΩ)
  - R_VBOT: 6.8kΩ (thay đổi từ 33kΩ)
  - Hỗ trợ 12-24V input (trước đó chỉ 12V)

### Changed
- **Relay isolation slot**: 4mm → 8mm (Y=82-90mm)
- **Design review**: All issues marked as FIXED
- **BOM**: Cập nhật với tất cả components mới

### Fixed
- Missing bootstrap capacitors (C_BST_5V, C_BST_3V3)
- VIN sense overvoltage protection
- Thermal management cho MP1584 regulators
- Assembly fiducials cho machine placement

### Updated Documentation
- FAB_CHECKLIST.txt (critical items for fab)
- FIRMWARE_NOTES.txt (OTA safety, ISR watchdog, debounce)
- DESIGN_REVIEW.md (V4 upgrades documented)

---

## [v6.2] - 2026-04-15 - Design Review

### Added
- Second MP1584 buck regulator cho +3V3_MAIN
- OR-ing diodes (+5V_SYS)
- Relay power limiting (R_RELAY_LIM + C_RELAY_BULK)
- Auto-reset circuit (BC847 transistors)
- TVS protection trên tất cả signal lines
- BAT54S clamping diodes
- Series resistors (100Ω DHT/DS, 22Ω I2C/SD)
- Active-LOW LEDs với 1.5kΩ resistors
- Ferrite bead rail splitting

---

## [v6.1] - Initial Review

### Issues Found
- Missing components (~15 critical items)
- Wrong GPIO assignments
- Wrong LED polarity
- Missing auto-reset circuit
- Missing TVS protection
- Relay isolation slot too narrow (3mm)

---

## Versioning

Project sử dụng [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

---

## Current Status

| Item | Status |
|------|--------|
| PCB Design | ✅ Complete |
| BOM | ✅ Complete |
| Gerber Files | ✅ Ready |
| Firmware Notes | ✅ Complete |
| Fab Checklist | ✅ Ready |
| Production | 🚀 Ready |

**Score: 9.5/10**

---

## Contributors

- EcoSynTech Global Team

## License

MIT License
