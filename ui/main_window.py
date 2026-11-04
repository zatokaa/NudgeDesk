"""Main Window orchestrator for NudgeDesk."""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config.theme import Theme
from config.constants import APP_NAME, APP_VERSION, STATUS_SYNCED, STATUS_SYNCING, STATUS_OFFLINE, STATUS_PENDING, get_asset_path
from utils.config_manager import config_manager
from utils.logger import logger
from database.db_manager import db
from database.models import Task, TaskList
from services.google_auth import google_auth
from services.sync_service import sync_service
from services.notification_service import notification_service
from services.tray_service import tray_service
from utils.memory_optimizer import trim_memory

from ui.sidebar import Sidebar
from ui.dashboard import Dashboard
from ui.task_view import TaskView
from ui.settings_view import SettingsView
from ui.dialogs import TaskDialog, NewListDialog, ConfirmDeleteDialog

class MainWindow(ctk.CTk):
    """NudgeDesk Main Desktop Application Window."""

    def __init__(self):
        super().__init__()
        
        # Configure application window
        self.title(f"{APP_NAME} – Google Tasks Companion")
        
        # Load theme setting
        palette_id = config_manager.get("theme_palette", "zest")
        Theme.apply_palette(palette_id)
        theme_mode = "light" if Theme.active.is_light else "dark"
        ctk.set_appearance_mode(theme_mode)
        self.configure(fg_color=Theme.BG_MAIN)

        # Restore window geometry
        width = config_manager.get("window_width", 1080)
        height = config_manager.get("window_height", 720)
        pos_x = config_manager.get("window_x")
        pos_y = config_manager.get("window_y")
        
        if pos_x is not None and pos_y is not None:
            self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        else:
            self.geometry(f"{width}x{height}")

        self.minsize(860, 580)

        # Set Window Icon
        icon_ico = get_asset_path("assets/icons/app_icon.ico")
        if icon_ico.exists():
            try:
                self.iconbitmap(str(icon_ico))
            except Exception:
                pass

        # State
        self.current_filter = config_manager.get("active_view", "my_day")
        self.current_list_id = None
        self.search_query = ""

        # Window protocols
        self.protocol("WM_DELETE_WINDOW", self._on_close_requested)
        self.bind("<Configure>", self._on_configure)

        # Setup Layout
        self._build_layout()

        # Connect Services Callbacks
        self._setup_service_callbacks()

        # Initial data load
        self.refresh_ui()

        # Periodic notification check (every 5 minutes)
        self.after(5000, self._periodic_reminder_check)

        # Initial memory trim and periodic GC (drops RAM down to ~10-20 MB)
        self.after(2500, self._periodic_memory_trim)

    def _build_layout(self) -> None:
        """Constructs the sidebar, dashboard, and content containers."""
        # Main layout frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar fixed
        self.grid_columnconfigure(1, weight=1)  # Content responsive

        # 1. Left Sidebar
        self.sidebar = Sidebar(
            self,
            on_navigate=self._handle_navigation,
            on_open_settings=self.show_settings,
            on_new_list=self._handle_new_list_prompt
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Right Content Area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=0) # Dashboard
        self.content_frame.grid_rowconfigure(1, weight=1) # Task view or Settings
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Dashboard Top
        self.dashboard = Dashboard(
            self.content_frame,
            on_add_task=self._handle_add_task_modal,
            on_sync_now=self._handle_manual_sync,
            on_search=self._handle_search,
            on_card_click=self._handle_bento_card_click
        )
        self.dashboard.grid(row=0, column=0, sticky="ew")

        # Task View Area
        self.task_view = TaskView(
            self.content_frame,
            on_toggle_complete=self._handle_toggle_complete,
            on_edit_task=self._handle_edit_task,
            on_delete_task=self._handle_delete_task,
            on_quick_add=self._handle_quick_add
        )
        self.task_view.grid(row=1, column=0, sticky="nsew")

        # Settings View (hidden initially)
        self.settings_view = SettingsView(
            self.content_frame,
            on_close=self.hide_settings,
            on_sync_now=self._handle_manual_sync,
            on_auth_trigger=self._handle_auth_trigger,
            on_theme_changed=self._handle_palette_change
        )

    def _setup_service_callbacks(self) -> None:
        """Attaches background worker notifications to safe UI thread dispatch."""
        sync_service.on_status_change = lambda status, msg: self.after(0, lambda: self._update_sync_ui(status, msg))
        sync_service.on_sync_completed = lambda: self.after(0, self.refresh_ui)
        google_auth.on_auth_changed = lambda authed, email: self.after(0, self._on_auth_changed)
        
        # Tray service integration
        tray_service.on_show_window = lambda: self.after(0, self.show_window)
        tray_service.on_sync_now = lambda: self.after(0, self._handle_manual_sync)
        tray_service.on_quick_add = lambda: self.after(0, self._handle_tray_quick_add)
        tray_service.on_exit_app = lambda: self.after(0, self.exit_app)

    # =========================================================================
    # Navigation & View Switching
    # =========================================================================

    def _handle_navigation(self, filter_type: str, list_id: Optional[str]) -> None:
        self.current_filter = filter_type
        self.current_list_id = list_id
        config_manager.set("active_view", filter_type)

        titles = {
            "my_day": "☀️ My Day",
            "all": "📋 All Tasks",
            "upcoming": "📅 Upcoming Tasks",
            "completed": "✅ Completed Tasks"
        }
        if filter_type == "list" and list_id:
            lst = db.get_list_by_id(list_id)
            view_title = f"📁 {lst.title if lst else 'Task List'}"
        else:
            view_title = titles.get(filter_type, "Tasks")

        self.task_view.set_title(view_title)
        self.hide_settings()
        self.refresh_task_list()

    def _handle_bento_card_click(self, target_filter: str) -> None:
        self.sidebar._handle_nav_click(target_filter)

    def show_settings(self) -> None:
        self.settings_view.refresh_state()
        self.task_view.grid_forget()
        self.dashboard.grid_forget()
        self.settings_view.grid(row=0, column=0, rowspan=2, sticky="nsew")

    def hide_settings(self) -> None:
        self.settings_view.grid_forget()
        self.dashboard.grid(row=0, column=0, sticky="ew")
        self.task_view.grid(row=1, column=0, sticky="nsew")
        self.refresh_ui()

    # =========================================================================
    # Data Refresh & Rendering
    # =========================================================================

    def refresh_ui(self) -> None:
        """Full refresh of tasks, lists, metrics, and sidebar state."""
        lists = db.get_all_lists()
        self.sidebar.update_task_lists(lists)
        
        counts = db.get_dashboard_counts()
        self.dashboard.update_metrics(counts)

        self.refresh_task_list()
        self.sidebar.update_sync_status(sync_service.current_status)

    def refresh_task_list(self) -> None:
        tasks = db.get_tasks(
            filter_type=self.current_filter,
            list_id=self.current_list_id,
            search=self.search_query
        )
        all_lists = db.get_all_lists()
        list_map = {lst.id: lst.title for lst in all_lists}
        for lst in all_lists:
            if lst.remote_id:
                list_map[lst.remote_id] = lst.title

        self.task_view.render_tasks(tasks, list_map)

    def _update_sync_ui(self, status: str, message: Optional[str]) -> None:
        self.sidebar.update_sync_status(status)

    def _on_auth_changed(self) -> None:
        self.sidebar.update_sync_status(sync_service.current_status)
        self.refresh_ui()
        if self.settings_view.winfo_ismapped():
            self.settings_view.refresh_state()

    def _handle_search(self, query: str) -> None:
        self.search_query = query
        self.refresh_task_list()

    def _handle_manual_sync(self) -> None:
        sync_service.trigger_sync()

    def _periodic_reminder_check(self) -> None:
        notification_service.check_and_notify_due_tasks()
        # Reschedule check every 5 minutes
        self.after(300000, self._periodic_reminder_check)

    def _periodic_memory_trim(self) -> None:
        trim_memory()
        # Reschedule memory trimming every 2 minutes while idle
        self.after(120000, self._periodic_memory_trim)

    # =========================================================================
    # Task Operations
    # =========================================================================

    def _handle_toggle_complete(self, task: Task) -> None:
        new_status = "needsAction" if task.is_completed else "completed"
        now_iso = datetime.utcnow().isoformat() + "Z"
        
        task.status = new_status
        task.completed_at = now_iso if new_status == "completed" else None
        task.local_updated_at = now_iso
        task.sync_status = STATUS_PENDING

        db.upsert_task(task)
        
        # Enqueue sync item
        db.enqueue_sync(
            action="update_task",
            entity_type="task",
            entity_id=task.id,
            remote_id=task.remote_id,
            payload={
                "list_id": task.list_id,
                "status": task.status
            }
        )

        self.refresh_ui()
        sync_service.trigger_sync()

    def _handle_quick_add(self, title: str, notes: Optional[str], due: Optional[str]) -> None:
        target_list_id = self.current_list_id
        if not target_list_id:
            d_list = db.get_default_list()
            target_list_id = d_list.id if d_list else "@default"

        new_task = Task(
            list_id=target_list_id,
            title=title,
            notes=notes or "",
            status="needsAction",
            due=due,
            priority=0,
            sync_status=STATUS_PENDING
        )
        db.upsert_task(new_task)

        db.enqueue_sync(
            action="create_task",
            entity_type="task",
            entity_id=new_task.id,
            payload={
                "list_id": target_list_id,
                "title": title,
                "notes": notes,
                "due": due
            }
        )

        self.refresh_ui()
        sync_service.trigger_sync()

    def _handle_add_task_modal(self) -> None:
        TaskDialog(
            self,
            default_list_id=self.current_list_id,
            on_save=lambda data: self._handle_quick_add_from_dialog(data)
        )

    def _handle_tray_quick_add(self) -> None:
        self.show_window()
        self._handle_add_task_modal()

    def _handle_quick_add_from_dialog(self, data: Dict[str, Any]) -> None:
        new_task = Task(
            list_id=data["list_id"],
            title=data["title"],
            notes=data.get("notes", ""),
            status="needsAction",
            due=data.get("due"),
            priority=data.get("priority", 0),
            sync_status=STATUS_PENDING
        )
        db.upsert_task(new_task)

        db.enqueue_sync(
            action="create_task",
            entity_type="task",
            entity_id=new_task.id,
            payload={
                "list_id": data["list_id"],
                "title": data["title"],
                "notes": data.get("notes"),
                "due": data.get("due")
            }
        )

        self.refresh_ui()
        sync_service.trigger_sync()

    def _handle_edit_task(self, task: Task) -> None:
        TaskDialog(
            self,
            task=task,
            on_save=lambda data: self._save_edited_task(task, data)
        )

    def _save_edited_task(self, task: Task, data: Dict[str, Any]) -> None:
        now_iso = datetime.utcnow().isoformat() + "Z"
        task.title = data["title"]
        task.notes = data.get("notes", "")
        task.due = data.get("due")
        task.priority = data.get("priority", 0)
        task.list_id = data["list_id"]
        task.local_updated_at = now_iso
        task.sync_status = STATUS_PENDING

        db.upsert_task(task)

        db.enqueue_sync(
            action="update_task",
            entity_type="task",
            entity_id=task.id,
            remote_id=task.remote_id,
            payload={
                "list_id": task.list_id,
                "title": task.title,
                "notes": task.notes,
                "due": task.due,
                "status": task.status
            }
        )

        self.refresh_ui()
        sync_service.trigger_sync()

    def _handle_delete_task(self, task: Task) -> None:
        ConfirmDeleteDialog(
            self,
            item_name=task.title,
            item_type="task",
            on_confirm=lambda: self._confirm_delete_task(task)
        )

    def _confirm_delete_task(self, task: Task) -> None:
        db.mark_task_deleted(task.id)
        db.enqueue_sync(
            action="delete_task",
            entity_type="task",
            entity_id=task.id,
            remote_id=task.remote_id,
            payload={"list_id": task.list_id}
        )
        self.refresh_ui()
        sync_service.trigger_sync()

    def _handle_new_list_prompt(self) -> None:
        NewListDialog(self, on_create=self._create_new_list)

    def _create_new_list(self, title: str) -> None:
        new_list = TaskList(title=title, sync_status=STATUS_PENDING)
        db.upsert_list(new_list)
        db.enqueue_sync(
            action="create_list",
            entity_type="task_list",
            entity_id=new_list.id,
            payload={"title": title}
        )
        self.refresh_ui()
        sync_service.trigger_sync()

    # =========================================================================
    # OAuth and Settings triggers
    # =========================================================================

    def _handle_auth_trigger(self, credentials_path: Optional[Path]) -> None:
        import threading
        
        def _run_auth():
            success, msg = google_auth.authenticate_interactive(credentials_path)
            if success:
                self.after(0, lambda: messagebox.showinfo("Connected", msg))
                sync_service.trigger_sync()
            else:
                self.after(0, lambda: messagebox.showwarning("Authentication", msg))

        auth_thread = threading.Thread(target=_run_auth, daemon=True)
        auth_thread.start()

    def _handle_palette_change(self, palette_id: str) -> None:
        palette = Theme.apply_palette(palette_id)
        config_manager.set("theme_palette", palette_id)
        theme_mode = "light" if palette.is_light else "dark"
        config_manager.set("theme_mode", theme_mode)
        ctk.set_appearance_mode(theme_mode)
        self.configure(fg_color=Theme.BG_MAIN)

        # Rebuild UI components to immediately reflect new palette styling
        for widget in self.winfo_children():
            widget.destroy()
        self._build_layout()
        self.refresh_ui()
        self.show_settings()

    # =========================================================================
    # Window State and System Tray
    # =========================================================================

    def _on_configure(self, event) -> None:
        # Save geometry if normal window state
        if self.state() == "normal" and event.widget == self:
            config_manager.set("window_width", self.winfo_width(), auto_save=False)
            config_manager.set("window_height", self.winfo_height(), auto_save=False)
            config_manager.set("window_x", self.winfo_x(), auto_save=False)
            config_manager.set("window_y", self.winfo_y(), auto_save=True)

    def hide_to_tray(self) -> None:
        """Hides main window while keeping tray process alive."""
        self.withdraw()
        trim_memory()

    def show_window(self) -> None:
        """Restores and brings main window to front."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_close_requested(self) -> None:
        if config_manager.get("minimize_to_tray", True):
            self.hide_to_tray()
        else:
            self.exit_app()

    def exit_app(self) -> None:
        """Full application termination."""
        sync_service.stop()
        tray_service.stop()
        self.destroy()
