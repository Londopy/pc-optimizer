# PC Optimizer Pro

> A professional Windows PC optimization suite for gaming rigs — fan control, RGB, debloat, and registry tuning in one tray app.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Features

| Module | What it does |
|---|---|
| **Dashboard** | Live CPU, GPU, RAM, temps, top processes |
| **Optimizer** | 17 registry/power tweaks — HAGS, MMCSS, CPU boost, Game Mode, TCP tuning, telemetry |
| **Fan Control** | Corsair AIO fan/pump curves via `liquidctl` — Silent / Balanced / Performance / Max presets |
| **RGB / Lighting** | All-device color control via OpenRGB SDK — static, breathing, rainbow |
| **Debloat** | Remove 35+ Windows bloatware packages with one click |
| **Settings** | Autostart, dependency checker, registry backup |

---

## Install (for end users)

1. Download the latest `PCOptimizerPro_Setup_vX.X.X.exe` from [Releases](https://github.com/Londopy/pc-optimizer/releases)
2. Run installer as Administrator
3. Launch from Desktop or Start Menu

---

## Build from source

### Prerequisites
- Python 3.11+
- Windows 10/11
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (for installer packaging)
- [OpenRGB](https://openrgb.org/) (for RGB control) running with SDK Server enabled

### Quick build
```bash
git clone https://github.com/Londopy/pc-optimizer
cd pc-optimizer
pip install -r requirements.txt
# Double-click build.bat  OR:
python -m PyInstaller pc_optimizer.spec
```

### Full installer build
```bash
# After PyInstaller build succeeds:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
# Output: installer\output\PCOptimizerPro_Setup_v1.0.0.exe
```

---

## Fan Control (liquidctl)

Requires [liquidctl](https://github.com/liquidctl/liquidctl) installed. iCUE must be **closed** — they conflict on the same USB device.

Supported Corsair devices: H100i, H115i, H150i, Hydro Platinum/Pro XT, Commander Core/Pro.

---

## RGB Control (OpenRGB)

Requires [OpenRGB](https://openrgb.org/) running with SDK Server enabled on port 6742.

```
OpenRGB.exe --server --startminimized
```

Supports Corsair, ASUS, MSI, Gigabyte, Razer, Logitech, NZXT, and 100+ more.

---

## Optimizer tweaks applied

- Ultimate Performance power plan
- CPU: 100% min/max, Aggressive boost, Win32PrioritySeparation=38
- Disable Core Parking
- HAGS (Hardware-Accelerated GPU Scheduling)
- Windows Game Mode
- MMCSS: GPU Priority 8, CPU Priority 6
- Disable Xbox Game Bar/DVR
- TCP: RSS, Nagle off, ECN off
- Disable telemetry + Advertising ID
- Disable Cortana
- Visual effects: Best performance
- High-resolution timer
- Windows Update: no auto-restart
- NVIDIA telemetry tasks disabled
- 15 background services disabled
- Startup bloat removed

---

## License

MIT — feel free to fork and share.

---

*Built for: i9-12900KS | RTX 3090 Ti | DDR4-4000 | Windows 11*
