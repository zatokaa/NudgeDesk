"""Windows System Tray Service for NudgeDesk."""

import threading
from pathlib import Path
from typing import Optional, Callable
from PIL import Image

from utils.logger import logger
from utils.config_manager import config_manager
from config.constants import APP_NAME

try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

class TrayService:
    """Provides Windows System Tray integration with minimize-to-tray and quick actions."""

    def __init__(self):
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None
        self.on_show_window: Optional[Callable[[], None]] = None
        self.on_sync_now: Optional[Callable[[], None]] = None
        self.on_quick_add: Optional[Callable[[], None]] = None
        self.on_exit_app: Optional[Callable[[], None]] = None

    def start(self) -> None:
        """Initializes and runs the system tray icon on a daemon thread."""
        if not PYSTRAY_AVAILABLE:
            logger.warning("pystray is not installed, system tray disabled.")
            return

        tray_icon_path = Path("assets/icons/tray_icon.png")
        if not tray_icon_path.exists():
            tray_icon_path = Path("assets/icons/app_icon.png")

        try:
            image = Image.open(tray_icon_path)
        except Exception as e:
            logger.error(f"Failed to load tray icon: {e}")
            return

        menu = pystray.Menu(
            item("Open NudgeDesk", self._handle_show, default=True),
            item("Quick Add Task", self._handle_quick_add),
            item("Sync Now", self._handle_sync_now),
            pystray.Menu.SEPARATOR,
            item("Exit", self._handle_exit)
        )

        self._icon = pystray.Icon(
            name=APP_NAME,
            icon=image,
            title=APP_NAME,
            menu=menu
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="NudgeDesk-TrayWorker")
        self._thread.start()
        logger.info("System tray icon started.")

    def stop(self) -> None:
        """Stops the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def _handle_show(self, icon=None, item=None) -> None:
        if self.on_show_window:
            self.on_show_window()

    def _handle_sync_now(self, icon=None, item=None) -> None:
        if self.on_sync_now:
            self.on_sync_now()

    def _handle_quick_add(self, icon=None, item=None) -> None:
        if self.on_quick_add:
            self.on_quick_add()

    def _handle_exit(self, icon=None, item=None) -> None:
        if self.on_exit_app:
            self.on_exit_app()

tray_service = TrayService()

