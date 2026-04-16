# EcoSynTech PCB v6.3 — Industrial Outdoor IoT Controller

**Thiết kế mạch in PCB cho hệ thống IoT nông nghiệp công nghiệp ngoài trời**  
*Industrial outdoor IoT controller PCB design for agricultural automation*

![KiCad](https://img.shields.io/badge/KiCad-6.x-green) ![PCB](https://img.shields.io/badge/PCB-2%20Layer-blue) ![Board](https://img.shields.io/badge/Size-200x150mm-red) ![ESP32](https://img.shields.io/badge/WiFi-BLE-orange)

## Tổng quan / Overview

Mạch điều khiển IoT công nghiệp dựa trên **ESP32-WROOM-32E** với:
- **4 relay 5V 10A** mở rộng lên **8 relay**
- **4 cảm biến tương tự** qua **ADS1115** (16-bit ADC)
- **Cảm biến nhiệt độ/độ ẩm** DHT22 + DS18B20
- **Cảm biến đất** độ ẩm đất
- **Hardware watchdog** TPL5010
- **USB-UART** CP2102 với auto-reset
- **MicroSD** log dữ liệu
- **I2C expansion** (MCP23017×2) — 16 GPIO mở rộng
- **BME280** (optional) + **OLED 0.96"** (optional)
- **Reverse polarity protection** + **Surge protection** (GDT/MOV/TVS)

## Thông số kỹ thuật / Specifications

| Thông số | Giá trị |
|----------|---------|
| Vi điều khiển | ESP32-WROOM-32E (dual-core 240MHz, WiFi+BLE) |
| Điện áp vào | 12V DC (9–24V tolerant) |
| Relay | 4× SRD-05VDC (10A SPDT), mở rộng 8× |
| ADC | ADS1115 (16-bit, 4 kênh, I2C) |
| Giao tiếp | WiFi, BLE, USB, UART, I2C, SPI |
| Kích thước | 200 × 150 mm |
| Lớp đồng | 2 lớp (35μm) |
| Độ dày | 1.6mm |
| Chiều dày đồng | 1oz (35μm) |

## Cấu trúc Schematic / Schematic Structure

```
EcoSynTech_V6_3_Final.kicad_sch (Root)
├── S01_Power_Input.kicad_sch      # Power Input & Protection 12V
├── S02_Buck_5V.kicad_sch         # Buck 12V→5V (MP1584 #1)
├── S03_Buck_3V3.kicad_sch        # Buck 12V→3.3V (MP1584 #2)
├── S04_Rail_Split.kicad_sch       # Rail Split + Power_Good
├── S05_OR_Diodes.kicad_sch        # OR-ing Diodes +5V_SYS
├── S06_ESP32_Core.kicad_sch       # ESP32-WROOM-32E Core
├── S07_USB_UART.kicad_sch         # USB-UART CP2102 + Auto-Reset
├── S08_Watchdog.kicad_sch         # Hardware Watchdog TPL5010
├── S09_Relay_Drivers.kicad_sch    # 4-CH Relay + Drivers + Interlock
├── S10_DHT22.kicad_sch            # DHT22 Sensor + TVS
├── S11_DS18B20.kicad_sch          # DS18B20 Sensor + TVS
├── S12_Soil_ADS.kicad_sch         # Soil Sensor + ADS1115 A3
├── S13_Vin_Sense.kicad_sch        # Battery/VIN Sense
├── S14_ADS1115.kicad_sch          # ADS1115 4-CH ADC
├── S15_I2C_Bus.kicad_sch          # I2C Bus + ESD + BME280 + OLED
├── S16_MicroSD.kicad_sch          # MicroSD Card
├── S17_IO_Expanders.kicad_sch     # MCP23017 IO Expanders
├── S18_Exp_Relays.kicad_sch       # Expansion Relays 5-8
├── S19_Debug_TP.kicad_sch         # Debug Header + Test Points
└── S20_External_Conn.kicad_sch     # External Connectors
```

## Nguồn điện / Power Architecture

```
12V_IN → F1(2A) → GDT/MOV → R_SURGE/L_SURGE → TVS → Q_PROTECT → +12V_PROTECTED
  → MP1584#1 → +5V_MAIN → D_MAIN/USB → +5V_SYS → R_RELAY_LIM → RELAY COILS
  → MP1584#2 → +3V3_MAIN → FB_ESP → +3V3_ESP (ESP32, MCP23017, BME280, OLED)
                              → FB_ANA → +3V3_ANA (ADS1115, DHT22, DS18B20)
```

## Tính năng an toàn / Safety Features

- **Reverse polarity protection** — P-MOSFET AO4407A
- **Surge protection** — GDT Bourns 2027-09-B + MOV 14D201K
- **TVS clamping** — SMBJ24A (power), SMBJ5.0A (signals)
- **Hardware watchdog** — TPL5010 (timeout ~1.63s)
- **Relay hardware interlock** — diode-OR của POWER_GOOD + BOOT_OK + firmware
- **Fuses** — 2A slow-blow (input), 500mA PTC (USB)

## GPIO Mapping

| GPIO | Chức năng |
|------|-----------|
| IO1 | UART0_TX / BOOT_OK (firmware) |
| IO3 | UART0_RX |
| IO4 | WATCHDOG_KICK (TPL5010 DONE) |
| IO5 | SD_CS |
| IO14 | RELAY4_DRV |
| IO16 | LED_WIFI (active-LOW) |
| IO17 | LED_MQTT (active-LOW) |
| IO18 | SD_SCK |
| IO19 | SD_MISO |
| IO21 | I2C_SDA |
| IO22 | I2C_SCL |
| IO23 | SD_MOSI |
| IO25 | RELAY3_DRV |
| IO26 | RELAY1_DRV |
| IO27 | RELAY2_DRV |
| IO32 | DS18B20_RAW |
| IO33 | DHT22_RAW |
| IO35 | VIN_SENSE_RAW |

## Tài liệu / Documentation

- `DESIGN_REVIEW.md` — Design review report
- `PCB_LAYOUT_V3.md` — PCB layout guide
- `EcoSynTech_V6_3_Final_BOM_V3.csv` — Bill of Materials

## Mở với KiCad / Opening in KiCad

```bash
# Clone repository
git clone https://github.com/ecosyntech68vn/EcoSynTech_PCB-for-IOT.git
cd EcoSynTech_PCB-for-IOT

# Open in KiCad 6/7/8
kicad EcoSynTech_V6_3_Final.kicad_pro

# Or open schematic only
eeschema EcoSynTech_V6_3_Final.kicad_sch
```

## BOM Sourcing

Đặt linh kiện tại LCSC hoặc các nhà cung cấp tương đương. BOM đầy đủ trong `EcoSynTech_V6_3_Final_BOM_V3.csv`.

## Second Source Options

| Linh kiện | Thay thế |
|-----------|----------|
| MP1584 | AP63205 (Buck 12V→5V/3.3V) |
| CP2102 | CH340C (USB-UART) |
| Relay SRD | HF46F/5-HS1 |

## License

MIT License — EcoSynTech Global
