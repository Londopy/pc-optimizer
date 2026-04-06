# PC Optimizer Pro

> A professional Windows PC optimization suite for gaming rigs — system tweaks, fan control, RGB lighting, and debloat in one tray app.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue?style=flat-square&logo=windows)
![liquidctl](https://img.shields.io/badge/liquidctl-1.16.0+-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Quick Install

**Option A — Python installer (easiest, recommended for friends)**
```
python PCOptimizerPro_Installer.py
```
Downloads Python if missing, installs all dependencies, clones the repo, creates a desktop shortcut. Four-step GUI.

**Option B — Pre-built .exe**
Download `PCOptimizerPro_Setup_vX.X.X.exe` from [Releases](https://github.com/Londopy/pc-optimizer/releases) and run as Administrator.

**Option C — Manual**
```bash
git clone https://github.com/Londopy/pc-optimizer
cd pc-optimizer
pip install -r requirements.txt
python src/main.py
```

---

## Features

| Module | Description |
|---|---|
| **Dashboard** | Live CPU load, GPU load/temp, RAM usage, top processes — updates every 1.5s |
| **Optimizer** | 17 one-click registry and power tweaks for gaming performance |
| **Fan Control** | Corsair AIO + Lian Li UNI FAN — per-port speed, presets, live RPM via liquidctl |
| **RGB / Lighting** | Global and per-device color control via OpenRGB SDK |
| **Debloat** | Remove 35+ Windows bloatware apps with Safe/Caution tags |
| **Settings** | Autostart toggle, dependency checker, registry backup/restore |

Runs minimized to the system tray. Left-click to show/hide, right-click for quick actions.

---

## Fan Control

Requires `liquidctl 1.16.0+`. The app auto-detects connected devices on the Fan Control page and switches the UI automatically.

```bash
pip install --upgrade liquidctl
```

### Corsair AIO
Supported: H100i, H115i, H150i, Hydro Platinum, Hydro Pro XT, Commander Core, Commander Pro.

- Fan: fixed % or curve (Silent / Balanced / Performance / Max presets)
- Pump: quiet / balanced / extreme mode
- Live readout: liquid temp, fan RPM, pump RPM

> **iCUE must be closed.** liquidctl and iCUE cannot share the USB device.

### Lian Li UNI FAN
Supported: SL, AL, SL-Infinity, SL V2, AL V2.

- Per-port speed control — UNI HUB ports 1–4 set independently
- Global control across all ports at once
- Presets: Silent 25% / Balanced 50% / Performance 75% / Max 100%
- Live per-port RPM readout

> **L-Connect 3 must be closed** before using liquidctl.

> Temperature-based curves are not supported via liquidctl for Lian Li devices. Use L-Connect 3 or [CoolerControl](https://gitlab.com/coolercontrol/coolercontrol) for curve-based control.

---

## RGB Control

Requires [OpenRGB](https://openrgb.org/) running with SDK Server enabled (Settings → SDK Server, port 6742).

```bash
# Launch OpenRGB headless in background:
OpenRGB.exe --server --startminimized
```

Supports 100+ brands: Corsair, ASUS, MSI, Gigabyte, Razer, Logitech, NZXT, and more.

---

## Optimizer Tweaks

| # | Tweak | Detail |
|---|---|---|
| 1 | Power plan | Ultimate Performance (falls back to High Performance if unavailable) |
| 2 | Sleep / Hibernate | Disabled for always-on performance |
| 3 | CPU state | Min/max locked to 100%, Aggressive boost mode |
| 4 | CPU priority | Win32PrioritySeparation = 38 (foreground boost) |
| 5 | Core Parking | Disabled — all cores stay active |
| 6 | HAGS | Hardware-Accelerated GPU Scheduling enabled |
| 7 | Game Mode | Windows Game Mode enabled |
| 8 | MMCSS | GPU Priority 8, CPU Priority 6, High scheduling category |
| 9 | Game Bar / DVR | Xbox Game Bar and background capture disabled |
| 10 | Network / TCP | RSS on, Nagle off, ECN off, timestamps off |
| 11 | Telemetry | Windows telemetry + Advertising ID disabled |
| 12 | Cortana | Disabled via Group Policy |
| 13 | Visual effects | Best performance mode |
| 14 | Timer resolution | GlobalTimerResolutionRequests enabled |
| 15 | Windows Update | No forced auto-restart with logged-on users |
| 16 | NVIDIA telemetry | 4 tracking scheduled tasks disabled |
| 17 | Background services | 15 unnecessary services stopped and disabled |
| +  | Startup cleanup | Common bloat removed from registry Run keys |

Each tweak can be toggled individually or run all at once. Risk level (Low / Medium) is shown per tweak.

---

## Debloat

Removes pre-installed Windows and OEM apps that run in the background. Each entry is tagged:

- **SAFE** — no core Windows functionality, safe to remove
- **CAUTION** — may affect some workflows (OneDrive, Mail, etc.)

35+ packages including Xbox apps, Cortana, Teams (personal), Candy Crush, Disney+, TikTok, Clipchamp, and more.

---

## Dependencies

| Package | Purpose | Required |
|---|---|---|
| `PyQt6` | UI framework | ✓ |
| `psutil` | CPU / RAM / process monitoring | ✓ |
| `pynvml` | NVIDIA GPU stats and fan lock | ✓ |
| `liquidctl` ≥ 1.16.0 | Corsair AIO + Lian Li UNI FAN control | For fan control |
| `openrgb-python` | RGB lighting via OpenRGB SDK | For RGB control |
| `HardwareMonitor` | CPU/GPU temps via LibreHardwareMonitor | Optional |
| `pywin32` | Windows registry / shortcuts | ✓ |
| `Pillow` | Icon generation | ✓ |

The Settings page has a built-in dependency checker with one-click install buttons.

---

## Build from Source

```bash
git clone https://github.com/Londopy/pc-optimizer
cd pc-optimizer
pip install -r requirements.txt

# Build standalone .exe (PyInstaller):
build.bat

# Or manually:
pyinstaller pc_optimizer.spec --noconfirm

# Package into installer (requires Inno Setup 6):
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
```

GitHub Actions automatically builds and publishes a release `.exe` when you push a version tag:
```bash
git tag v1.0.1
git push --tags
```

---

## License

MIT — fork it, share it, do whatever.

---

*Built for: i9-12900KS · RTX 3090 Ti · DDR4-4000 · Windows 11*
