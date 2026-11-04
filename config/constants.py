"""Constants and configuration defaults for NudgeDesk."""

import os
from pathlib import Path

APP_NAME = "NudgeDesk"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Lightweight Google Tasks Desktop Companion for Windows 11"

# Application Data Directory
APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# Database and Config Paths
DATABASE_PATH = APPDATA_DIR / "nudgedesk.db"
CONFIG_FILE_PATH = APPDATA_DIR / "config.json"
CREDENTIALS_FILE_PATH = APPDATA_DIR / "credentials.json"
TOKEN_CACHE_FILE = APPDATA_DIR / "token.json"
LOG_FILE_PATH = APPDATA_DIR / "nudgedesk.log"

# Default Sync Settings
DEFAULT_SYNC_INTERVAL_SECONDS = 300  # 5 minutes
MIN_SYNC_INTERVAL_SECONDS = 60      # 1 minute
MAX_SYNC_INTERVAL_SECONDS = 3600    # 1 hour

# Google Tasks API Scopes
GOOGLE_TASKS_SCOPES = [
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# Sync Statuses
STATUS_SYNCED = "synced"
STATUS_PENDING = "pending"
STATUS_SYNCING = "syncing"
STATUS_ERROR = "error"
STATUS_OFFLINE = "offline"

# Task Priorities
PRIORITY_NONE = 0
PRIORITY_LOW = 1
PRIORITY_MEDIUM = 2
PRIORITY_HIGH = 3

PRIORITY_LABELS = {
    PRIORITY_NONE: "None",
    PRIORITY_LOW: "Low",
    PRIORITY_MEDIUM: "Medium",
    PRIORITY_HIGH: "High",
}

PRIORITY_COLORS = {
    PRIORITY_NONE: "#6B7280",
    PRIORITY_LOW: "#3B82F6",
    PRIORITY_MEDIUM: "#F59E0B",
    PRIORITY_HIGH: "#EF4444",
}

