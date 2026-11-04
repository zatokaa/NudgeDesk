"""Windows Registry Startup manager."""

import sys
import winreg
from pathlib import Path
from utils.logger import logger
from config.constants import APP_NAME

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

def set_start_with_windows(enable: bool) -> bool:
    """Enables or disables automatic startup with Windows."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )
        
        if enable:
            # If running as script vs frozen executable
            if getattr(sys, 'frozen', False):
                app_path = f'"{sys.executable}" --minimized'
            else:
                script_path = Path(__file__).resolve().parent.parent / "main.py"
                app_path = f'"{sys.executable}" "{script_path}" --minimized'
                
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
            logger.info(f"Registered Windows startup command: {app_path}")
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                logger.info("Removed Windows startup entry.")
            except FileNotFoundError:
                pass
                
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logger.error(f"Failed to configure Windows startup: {e}")
        return False

def is_start_with_windows_enabled() -> bool:
    """Checks whether the application is configured to start with Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return bool(val)
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False

