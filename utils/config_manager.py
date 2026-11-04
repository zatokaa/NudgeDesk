"""Persistent application configuration manager."""

import json
from typing import Any, Dict
from config.constants import CONFIG_FILE_PATH, DEFAULT_SYNC_INTERVAL_SECONDS
from utils.logger import logger

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme_mode": "dark",  # "dark", "light", "system"
    "theme_palette": "zest",  # "warm_linen", "emerald_pure", "nordic_frost", "zest", "slate_pro", "midnight_oled"
    "sync_interval": DEFAULT_SYNC_INTERVAL_SECONDS,
    "auto_sync": True,
    "start_with_windows": False,
    "minimize_to_tray": True,
    "launch_minimized": False,
    "notifications_enabled": True,
    "window_width": 1080,
    "window_height": 720,
    "window_x": None,
    "window_y": None,
    "active_view": "my_day",
    "account_email": None,
    "account_name": None,
    "last_sync_timestamp": None,
}

class ConfigManager:
    """Manages application settings loaded from/saved to config.json."""

    def __init__(self):
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> None:
        if CONFIG_FILE_PATH.exists():
            try:
                data = json.loads(CONFIG_FILE_PATH.read_text(encoding="utf-8"))
                self._config.update(data)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                self.save()
        else:
            self.save()

    def save(self) -> None:
        try:
            CONFIG_FILE_PATH.write_text(json.dumps(self._config, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        self._config[key] = value
        if auto_save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        return self._config.copy()

config_manager = ConfigManager()

