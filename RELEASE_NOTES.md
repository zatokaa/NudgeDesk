# 🔔 NudgeDesk v1.1.0 Release Notes
> **Release Version:** `v1.1.0`  
> **Target OS:** Windows 11 / Windows 10 (64-bit)  
> **Release Type:** Standalone Portable Windows Executable & Source Code

---

## 🌟 Executive Summary

**NudgeDesk v1.1.0** represents a major milestone in delivering an ultra-lightweight, native Windows 11 companion for Google Tasks. This release introduces a brand-new app icon, a curated 6-palette Bento Box theme system with live switching, a native Windows PSAPI memory optimizer that drops idle RAM footprint down to ~5–65 MB, enhanced single-instance window wake-up, and bulletproof offline synchronization.

---

## 🚀 What's New in v1.1.0

### 1. 🎨 New Official App Icon & Asset Packaging
- **High-DPI App Icon**: Integrated the official brand icon into the window title bar, Windows taskbar, and notification tray.
- **Universal Asset Resolution**: Introduced `get_asset_path()` to guarantee icons and theme assets always load flawlessly whether running from source, a Windows shortcut, Windows startup, or a bundled single-file executable.

---

### 2. 🌈 6 Curated Theme Palettes with Live Switching
Transform your workspace aesthetics directly from **⚙️ Settings** with 6 bespoke color palettes matching modern design standards:

| Theme Name | Appearance | Primary Accent | Canvas / Tone | Best For |
|---|---|---|---|---|
| 🌾 **Warm Linen** *(Solara)* | ☀️ Light | Terracotta Coral (`#D9534F`) | Organic Cream (`#F7F3EB`) | Daytime deep focus & writing |
| 🌿 **Emerald Pure** *(Mint)* | ☀️ Light | Vibrant Forest Emerald (`#059669`) | Crisp Mint-White (`#F2FAF5`) | Calm, balanced productivity |
| ❄️ **Nordic Frost** *(Glacier)* | ☀️ Light | Glacier Sky Blue (`#0284C7`) | Pearl Arctic White (`#F0F7FB`) | High clarity & crisp layouts |
| ⚡ **Zest** *(Amber Gold)* | 🌙 Dark | Radiant Amber Gold (`#F5C542`) | Charcoal Onyx (`#111318`) | Night focus & official brand theme |
| 💎 **Slate Pro** *(Apple Blue)* | 🌙 Dark | Apple iOS Blue (`#0A84FF`) | Deep Technical Slate (`#0F172A`) | Developer & technical workflows |
| 🌌 **Midnight OLED** *(Indigo)* | 🌙 Dark | Electric Indigo (`#6366F1`) | True Pitch Black (`#000000`) | OLED displays & maximum battery savings |

*All palettes switch live across sidebar, cards, buttons, badges, and text with zero application restart required.*

---

### 3. 🪶 Ultra-Low RAM Engine (~50–65 MB / ~5 MB in Tray)
Most desktop productivity tools (Slack, Teams, Notion) rely on heavy Chromium/Electron runtimes that consume 400 MB to 800 MB+ of RAM.

NudgeDesk utilizes native Windows Kernel memory optimization:
- **Automatic Working Set Trimming**: Calls `ctypes.windll.psapi.EmptyWorkingSet` to flush unneeded committed pages back to Windows.
- **Trigger Points**:
  - 2.5 seconds post-startup (after initial widget rendering).
  - Immediately following each Google Tasks sync pass.
  - Automatically upon minimizing to the system tray (dropping memory down to **~5.1 MB**).
  - Periodically every 2 minutes while idle.

---

### 4. 🪟 Duplicate Process Guard & Foreground Window Activation
- **Single-Instance Win32 Mutex**: Prevents multiple background instances from spawning.
- **Smart Window Activation**: If NudgeDesk is already running (e.g. minimized in the tray) and the executable is launched again, it automatically locates the running instance using Win32 `EnumWindows`, calls `ShowWindow(SW_RESTORE)` and `SetForegroundWindow`, bringing your tasks to the front instantly before exiting the second process.

---

### 5. 🔄 Google Tasks Synchronization & Offline Queue
- **Reconciliation Fix**: Fixed a status resolution error during local cache merging so sync status accurately reports **● Synced**.
- **Two-Way Sync**: Fast, non-blocking background worker thread coordinates changes with Google Tasks API v1 without freezing the UI.
- **Full Offline Support**: Tasks created, modified, or completed while offline are stored in the SQLite `sync_queue` and automatically flushed when your connection returns.
- **Silent Token Refresh**: Automatic OAuth 2.0 token refreshes in the background.

---

### 6. 📋 Production Logging & Security Hardening
- **Rotating Log File**: Upgraded `nudgedesk.log` to a `RotatingFileHandler` (2 MB limit, 2 rolling backups).
- **Windowed Crash Protection**: Handled `sys.stdout is None` scenarios to prevent crashes when running without a console.
- **Sanitized Repository**: Removed all machine-specific paths from `.spec` files using relative directory resolution. Added `.gitignore` to prevent local credentials or secrets from being tracked.

---

## 💻 Download & Installation

### Option 1: Standalone Portable Executable (Recommended)
No installation or Python runtime required:
1. Download **`NudgeDesk.exe`** from `dist/NudgeDesk.exe`.
2. Move it to your preferred folder (e.g., `C:\Program Files` or your User folder).
3. Double-click to launch.

### Option 2: Run from Python Source
```powershell
git clone https://github.com/your-username/nudgedesk.git
cd nudgedesk
pip install -r requirements.txt
python main.py
```

---

## ⚙️ System Requirements

- **Operating System:** Windows 11 or Windows 10 (64-bit)
- **RAM:** Less than 70 MB (typically ~5–55 MB idle)
- **Disk Space:** ~50 MB
- **Network:** Internet connection required for Google Tasks sync; fully functional offline for local tasks.

---

## 📄 License & Terms

Free of charge for personal and community use. Anyone is free to use, modify, and upgrade the application. Commercial resale or distribution for profit is prohibited.

Copyright © 2026 [PremiumBayy](https://www.premiumbayy.com/). All Rights Reserved.

