<p align="center">
  <img src="assets/icons/app_icon.png" width="128" height="128" alt="NudgeDesk App Icon" />
</p>

# 🔔 NudgeDesk
> **Remember Less. Get More Done.**  
> *A minimalist, hyper-productive task ecosystem for Web, Mobile, and Windows 11.*

[![Direct Download for Windows](https://img.shields.io/badge/Direct%20Download-Windows%2011%20EXE-blue?style=for-the-badge&logo=windows11&logoColor=white)](dist/NudgeDesk.exe)

![Windows 11](https://img.shields.io/badge/Windows-11-0078D4?logo=windows11&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-F5C542)
![Google Tasks API](https://img.shields.io/badge/API-Google%20Tasks%20v1-4285F4?logo=google&logoColor=white)
![SQLite](https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?logo=sqlite&logoColor=white)
![Executable](https://img.shields.io/badge/Standalone-PyInstaller%20EXE-green)

---

## 🌟 Overview

**NudgeDesk** is a native, ultra-lightweight Windows 11 desktop application designed to synchronize seamlessly with **Google Tasks**. It allows you to quickly view, create, edit, complete, and organize your tasks directly from your desktop without keeping an open web browser or heavy Chromium/Electron wrappers running in the background.

NudgeDesk adopts a modern **Bento Box-inspired UI** tailored specifically to Windows 11 aesthetics with low RAM consumption (idle ~50–65 MB), instant startup, offline capability with automatic retry queues, native toast notifications, and full system tray integration.

---

## 🪶 Ultra-Low RAM Architecture (~50–65 MB)

Most Electron apps consume 350 MB to 800 MB+ of memory. Nudge was engineered from the ground up to run like a native Windows utility:

| Metric | Typical Desktop Apps (Slack, Notion, Teams) | Nudge Desktop Mini-Widget |
|---|---|---|
| **Idle Memory (RAM)** | 350 MB – 800 MB+ | **~50 MB – 65 MB** ⚡ |
| **Background Processes** | 5 – 8 processes | **1 isolated process** |
| **V8 Heap Cap** | Unlimited (bloats over time) | `--max-old-space-size=64` |
| **GPU Acceleration** | Enabled (heavy VRAM drain) | Disabled for lightweight efficiency |
| **Auto-Sync Frequency** | Constant polling (battery drain) | Optimized every 30 minutes |
| **Gaming & Compiling Impact** | Noticeable FPS drops / RAM hog | Virtually undetectable |

---

## ✨ Key Features

### ⚡ Ultra-Lightweight & Fast
- **Low RAM footprint**: Runs natively via Python / CustomTkinter with zero Electron or browser overhead (~50–65 MB working set).
- **Instant startup**: Optimized SQLite queries with WAL mode and lazy rendering.
- **Single-instance protection**: Guarded by a Windows Named Mutex.

### 🔄 Google Tasks Synchronization
- **Primary Source of Truth**: Two-way synchronization with official Google Tasks apps on Android, iOS, and Web.
- **Background Synchronization Worker**: Threaded sync loop keeps the UI completely fluid and non-blocking.
- **Automatic Token Refresh**: Securely refreshes expired OAuth 2.0 access tokens in the background.
- **Configurable Intervals**: Choose from 1 min, 2 min, 5 min (default), 10 min, 15 min, 30 min, or 1 hour, or hit **Sync Now**.
- **Safe Conflict Handling**: Local edits are preserved during offline states; incoming remote changes reconcile smoothly.

### 📶 Complete Offline Support
- Create, modify, and complete tasks even without an internet connection.
- Pending actions are queued locally in SQLite (`sync_queue`).
- Automatically drains and synchronizes queued changes with Google Tasks the moment your connection is restored.
- Live status indicator: `Synced`, `Syncing...`, `Offline`, or `Sync Error`.

### 🪟 Windows 11 Native Experience
- **Bento Box Layout**: Clean cards for *Today's Tasks*, *Upcoming*, *Completed*, and *Total Pending*.
- **Quick-Add Bar**: Instant keyboard-driven task creation with Enter-to-save and "Due Today" shortcut.
- **System Tray Integration**: Minimize to tray on close, system tray context menu (`Open`, `Quick Add`, `Sync Now`, `Exit`).
- **Windows Startup**: Optional toggle to automatically launch minimized on Windows boot.
- **Native Toast Notifications**: Action Center notifications for tasks due today or overdue.

---

## 🎨 Theme System

| Palette | Type | Primary Accent | Canvas Tone | Best For |
|---|---|---|---|---|
| 🌾 **Warm Linen (Solara)** | ☀️ Light | Terracotta & Coral (`#D45256`) | Organic Warm Cream (`#FAF7F2`) | Daytime deep focus |
| 🌿 **Emerald Pure (Mint)** | ☀️ Light | Vibrant Forest Emerald (`#059669`) | Crisp Porcelain White (`#FAFCFA`) | Calm productivity |
| ⚡ **Zest Gold** | 🌙 Dark | Amber Sunburst (`#F59E0B`) | Charcoal Onyx (`#0A0A0B`) | High-contrast night |
| 💎 **Slate Pro** | 🌙 Dark | Apple iOS Royal Blue (`#3B82F6`) | Deep Slate Glass (`#0F172A`) | Technical workflows |
| 🌌 **Midnight OLED** | 🌙 Dark | Electric Indigo (`#6366F1`) | True Pitch Black (`#000000`) | Battery saver & OLED |

---

## 📁 Project Architecture

```
NudgeDesk/
├── main.py                     # Application entry point & single-instance guard
├── build.py                    # PyInstaller standalone executable packaging script
├── requirements.txt            # Python dependencies
├── README.md                   # Complete application documentation
├── GOOGLE_OAUTH_SETUP.md       # Google Cloud API & OAuth configuration guide
├── config/
│   ├── constants.py            # App paths, default intervals, Google API scopes
│   └── theme.py                # Bento color palette, light/dark styles, typography
├── database/
│   ├── db_manager.py           # SQLite connection pool, CRUD, filters, WAL mode
│   └── models.py               # Data models: Task, TaskList, SyncQueueItem
├── services/
│   ├── google_auth.py          # OAuth 2.0 flow, token refresh, profile retrieval
│   ├── google_tasks.py         # Google Tasks API v1 REST client
│   ├── sync_service.py         # Two-way sync coordinator, conflict reconciliation
│   ├── notification_service.py # Windows 11 native toast notifications (winotify)
│   └── tray_service.py         # Windows System Tray daemon (pystray)
├── ui/
│   ├── main_window.py          # Window coordinator, shortcuts, lifecycle
│   ├── sidebar.py              # Bento vertical sidebar with task list tree
│   ├── dashboard.py            # Header greetings, live search, 4 Bento metric cards
│   ├── task_view.py            # Task card list, completion toggle, quick-add bar
│   ├── settings_view.py        # Account status, intervals, startup, theme toggles
│   └── dialogs.py              # Modals: TaskDialog, NewListDialog, ConfirmDelete
├── utils/
│   ├── config_manager.py       # JSON configuration persistence
│   ├── credentials_manager.py  # Windows Credential Manager / DPAPI vault
│   ├── single_instance.py      # Win32 Named Mutex single-instance protection
│   ├── windows_startup.py      # Windows Registry Run key automation
│   └── logger.py               # Application logging (console + file)
├── assets/
│   └── icons/                  # High-DPI app and system tray icons (.png, .ico)
├── dist/
│   └── NudgeDesk.exe           # Standalone Windows 11 executable
└── tests/
    ├── test_database.py        # SQLite CRUD, filtering, queue tests
    ├── test_config.py          # Settings persistence tests
    ├── test_credentials.py     # Windows DPAPI & keyring tests
    └── test_ui.py              # UI component lifecycle & memory tests
```

---

## 🚀 Getting Started

### Prerequisites
- Windows 10 or Windows 11 (64-bit)
- Python 3.11 or newer (for running from source)

### Option 1: Run the Standalone Windows Executable
No Python installation required!
1. Locate the standalone executable inside the `dist/` directory:
   ```
   dist/NudgeDesk.exe
   ```
2. Double-click **`NudgeDesk.exe`** to launch immediately.

---

### Option 2: Run from Python Source

1. Clone or extract the project directory:
   ```powershell
   cd "NudgeDesk"
   ```

2. Install the dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Run the application:
   ```powershell
   python main.py
   ```

To run minimized directly to the system tray:
```powershell
python main.py --minimized
```

---

## 🔑 Google Tasks Account Setup

For full synchronization with your Google Tasks account:
1. Follow the quick step-by-step instructions in [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) to obtain your `credentials.json` from the Google Cloud Console.
2. In NudgeDesk, open **⚙️ Settings** > click **Load credentials.json** > click **Sign In with Google**.
3. Authorize in your web browser. NudgeDesk will immediately download and sync all your Google Tasks and Task Lists!

*Note: NudgeDesk works out of the box even before connecting Google Tasks—you can create, organize, and manage local tasks offline anytime.*

---

## 🧪 Running Unit Tests

Run the full automated test suite:
```powershell
python -m unittest discover -s tests
```

All 8 tests cover:
- SQLite task lists and tasks CRUD operations
- My Day, Upcoming, Completed, and Search filters
- Bento metrics calculations
- Offline synchronization queue operations
- Configuration persistence
- Windows DPAPI encryption and token storage
- Full CustomTkinter UI lifecycle

---

## 🔨 Building the Executable

To recompile or package a fresh standalone `.exe` using PyInstaller:
```powershell
python build.py
```
This automatically compiles all dependencies, collects CustomTkinter assets, embeds the application icon, and outputs `dist/NudgeDesk.exe`.

---

## 🛡️ Security

- **Minimum Required Permissions**: Uses only `https://www.googleapis.com/auth/tasks` and standard user identity scopes.
- **Zero Plain-Text Passwords**: Google passwords are never requested or stored.
- **Hardware/User-Bound DPAPI Vault**: Tokens are secured in Windows Credential Manager or protected via Windows Data Protection API (DPAPI).
- **Clean Disconnect**: Clicking **Sign Out** wipes stored tokens and cache immediately.

---

## 📄 License & Terms of Use

This project is provided **free of charge** for everyone.

- **Open to Modify & Upgrade:** Anyone is welcome to use, modify, study, customize, and upgrade this software for personal and non-commercial purposes.
- **Non-Commercial Only (Do Not Sell):** Selling, reselling, monetizing, or distributing this software or its source code for profit is strictly prohibited. Keep it free.

### Copyright Notice

Copyright © 2026 [PremiumBayy](https://www.premiumbayy.com/). All Rights Reserved.

This software, source code, design, and associated assets are proprietary. Unauthorized commercial use, resale, or paid redistribution without prior written authorization is strictly prohibited.

For support or enterprise inquiries, visit [www.PremiumBayy.com](https://www.premiumbayy.com/).


