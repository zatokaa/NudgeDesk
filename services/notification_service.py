"""Windows 11 Toast Notification Service for NudgeDesk."""

import threading
from datetime import datetime, date
from pathlib import Path
from typing import Set

from config.constants import APP_NAME, get_asset_path
from utils.config_manager import config_manager
from utils.logger import logger
from database.db_manager import db

try:
    from winotify import Notification, audio
    WINOTIFY_AVAILABLE = True
except ImportError:
    WINOTIFY_AVAILABLE = False

class NotificationService:
    """Manages native Windows 11 toast notifications for upcoming and overdue tasks."""

    def __init__(self):
        self._notified_tasks: Set[str] = set()
        self._icon_path = get_asset_path("assets/icons/app_icon.png")

    def send_notification(self, title: str, message: str) -> bool:
        """Sends an immediate Windows 11 toast notification."""
        if not config_manager.get("notifications_enabled", True):
            return False

        if not WINOTIFY_AVAILABLE:
            logger.info(f"[Toast] {title}: {message}")
            return False

        try:
            toast = Notification(
                app_id=APP_NAME,
                title=title,
                msg=message,
                icon=str(self._icon_path) if self._icon_path.exists() else None
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
            return True
        except Exception as e:
            logger.warning(f"Could not display toast notification: {e}")
            return False

    def check_and_notify_due_tasks(self) -> None:
        """Checks for tasks due today that have not yet been notified in this session."""
        if not config_manager.get("notifications_enabled", True):
            return

        try:
            tasks = db.get_tasks(filter_type="my_day")
            today_str = date.today().isoformat()
            
            for task in tasks:
                if task.id not in self._notified_tasks and task.status == "needsAction":
                    self._notified_tasks.add(task.id)
                    due_label = "today" if task.due == today_str else "overdue"
                    self.send_notification(
                        title=f"Task Reminder ({due_label.capitalize()})",
                        message=f"{task.title}\n{task.notes if task.notes else ''}".strip()
                    )
                    break # Send one polite notification at a time
        except Exception as e:
            logger.error(f"Error checking due tasks for notifications: {e}")

notification_service = NotificationService()

