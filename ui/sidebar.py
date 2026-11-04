"""Sidebar navigation component for NudgeDesk."""

import customtkinter as ctk
from PIL import Image
from typing import Callable, Optional, Dict, List
from pathlib import Path

from config.theme import Theme
from config.constants import APP_NAME, STATUS_SYNCED, STATUS_SYNCING, STATUS_OFFLINE, STATUS_ERROR
from database.models import TaskList
from utils.config_manager import config_manager

class Sidebar(ctk.CTkFrame):
    """Modern Bento-styled vertical sidebar."""

    def __init__(self, master, on_navigate: Callable[[str, Optional[str]], None], on_open_settings: Callable[[], None], on_new_list: Callable[[], None], **kwargs):
        super().__init__(master, fg_color=Theme.BG_SIDEBAR, width=240, corner_radius=0, **kwargs)
        self.pack_propagate(False)
        
        self.on_navigate = on_navigate
        self.on_open_settings = on_open_settings
        self.on_new_list = on_new_list
        self.active_item = "my_day"
        self.active_list_id = None
        
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.list_buttons: Dict[str, ctk.CTkButton] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        # Top Logo & App Title
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=16, pady=(16, 12))
        header_frame.pack_propagate(False)

        # App Icon
        icon_path = Path("assets/icons/app_icon.png")
        if icon_path.exists():
            try:
                pil_img = Image.open(icon_path)
                app_icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(28, 28))
                icon_lbl = ctk.CTkLabel(header_frame, image=app_icon, text="")
                icon_lbl.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        # Title Label
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="y", expand=True)

        title_lbl = ctk.CTkLabel(
            title_box,
            text=APP_NAME,
            font=Theme.get_font(18, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w")

        version_lbl = ctk.CTkLabel(
            title_box,
            text="Google Tasks Companion",
            font=Theme.get_font(10),
            text_color=Theme.TEXT_MUTED
        )
        version_lbl.pack(anchor="w", pady=(0, 0))

        # Divider
        ctk.CTkFrame(self, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        # Core Navigation Items
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.pack(fill="x", padx=10, pady=0)

        nav_items = [
            ("my_day", "☀️  My Day"),
            ("all", "📋  All Tasks"),
            ("upcoming", "📅  Upcoming"),
            ("completed", "✅  Completed"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                nav_container,
                text=label,
                anchor="w",
                font=Theme.get_font(13, "bold" if key == self.active_item else "normal"),
                fg_color=Theme.BG_CARD_HOVER if key == self.active_item else "transparent",
                hover_color=Theme.BG_CARD_HOVER,
                text_color=Theme.ACCENT if key == self.active_item else Theme.TEXT_PRIMARY,
                height=38,
                corner_radius=8,
                command=lambda k=key: self._handle_nav_click(k)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        # Divider before Task Lists
        ctk.CTkFrame(self, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=16, pady=12)

        # Task Lists Section Header
        lists_header = ctk.CTkFrame(self, fg_color="transparent")
        lists_header.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            lists_header,
            text="TASK LISTS",
            font=Theme.get_font(11, "bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(side="left")

        # "+ New List" small button
        add_list_btn = ctk.CTkButton(
            lists_header,
            text="+",
            width=22,
            height=22,
            font=Theme.get_font(14, "bold"),
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.ACCENT,
            command=self.on_new_list
        )
        add_list_btn.pack(side="right")

        # Scrollable area for dynamic Task Lists
        self.lists_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.BG_CARD_HOVER
        )
        self.lists_scroll.pack(fill="both", expand=True, padx=6, pady=0)

        # Bottom Frame (Account & Settings)
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=12)

        # Settings Button
        settings_btn = ctk.CTkButton(
            bottom_frame,
            text="⚙️  Settings",
            anchor="w",
            font=Theme.get_font(13),
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            height=36,
            corner_radius=8,
            command=self.on_open_settings
        )
        settings_btn.pack(fill="x", pady=(0, 8))

        # Account Status Bento Card
        self.account_card = ctk.CTkFrame(
            bottom_frame,
            fg_color=Theme.BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=Theme.BORDER
        )
        self.account_card.pack(fill="x", pady=(0, 2))

        self.account_email_lbl = ctk.CTkLabel(
            self.account_card,
            text="Not Connected",
            font=Theme.get_font(11, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        )
        self.account_email_lbl.pack(fill="x", padx=10, pady=(6, 0))

        # Status Pill Frame
        status_pill_frame = ctk.CTkFrame(self.account_card, fg_color="transparent")
        status_pill_frame.pack(fill="x", padx=10, pady=(2, 6))

        self.status_dot = ctk.CTkLabel(
            status_pill_frame,
            text="●",
            font=Theme.get_font(10),
            text_color=Theme.TEXT_MUTED
        )
        self.status_dot.pack(side="left", padx=(0, 4))

        self.status_lbl = ctk.CTkLabel(
            status_pill_frame,
            text="Offline",
            font=Theme.get_font(11),
            text_color=Theme.TEXT_MUTED
        )
        self.status_lbl.pack(side="left")

        # Make account card clickable to open settings
        self.account_card.bind("<Button-1>", lambda e: self.on_open_settings())
        self.account_email_lbl.bind("<Button-1>", lambda e: self.on_open_settings())
        self.status_lbl.bind("<Button-1>", lambda e: self.on_open_settings())

    def update_task_lists(self, task_lists: List[TaskList]) -> None:
        """Refreshes the dynamic task lists list in the sidebar."""
        for widget in self.lists_scroll.winfo_children():
            widget.destroy()
        self.list_buttons.clear()

        for t_list in task_lists:
            is_active = (self.active_item == "list" and self.active_list_id == t_list.id)
            title = f"📁  {t_list.title}"
            
            btn = ctk.CTkButton(
                self.lists_scroll,
                text=title,
                anchor="w",
                font=Theme.get_font(12, "bold" if is_active else "normal"),
                fg_color=Theme.BG_CARD_HOVER if is_active else "transparent",
                hover_color=Theme.BG_CARD_HOVER,
                text_color=Theme.ACCENT if is_active else Theme.TEXT_PRIMARY,
                height=32,
                corner_radius=6,
                command=lambda lid=t_list.id: self._handle_list_click(lid)
            )
            btn.pack(fill="x", pady=1)
            self.list_buttons[t_list.id] = btn

    def _handle_nav_click(self, key: str) -> None:
        self.active_item = key
        self.active_list_id = None
        self._update_highlight()
        self.on_navigate(key, None)

    def _handle_list_click(self, list_id: str) -> None:
        self.active_item = "list"
        self.active_list_id = list_id
        self._update_highlight()
        self.on_navigate("list", list_id)

    def _update_highlight(self) -> None:
        # Reset core nav
        for k, btn in self.nav_buttons.items():
            if k == self.active_item:
                btn.configure(fg_color=Theme.BG_CARD_HOVER, text_color=Theme.ACCENT, font=Theme.get_font(13, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_PRIMARY, font=Theme.get_font(13, "normal"))

        # Reset list nav
        for lid, btn in self.list_buttons.items():
            if self.active_item == "list" and lid == self.active_list_id:
                btn.configure(fg_color=Theme.BG_CARD_HOVER, text_color=Theme.ACCENT, font=Theme.get_font(12, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_PRIMARY, font=Theme.get_font(12, "normal"))

    def update_sync_status(self, status: str, account_email: Optional[str] = None) -> None:
        """Updates the status pill and account email label."""
        if account_email:
            display_email = account_email if len(account_email) <= 24 else account_email[:21] + "..."
            self.account_email_lbl.configure(text=display_email)
        else:
            saved_email = config_manager.get("account_email")
            if saved_email:
                display_email = saved_email if len(saved_email) <= 24 else saved_email[:21] + "..."
                self.account_email_lbl.configure(text=display_email)
            else:
                self.account_email_lbl.configure(text="Not Connected")

        if status == STATUS_SYNCED:
            self.status_dot.configure(text_color=Theme.SUCCESS)
            self.status_lbl.configure(text="Synced", text_color=Theme.SUCCESS)
        elif status == STATUS_SYNCING:
            self.status_dot.configure(text_color=Theme.WARNING)
            self.status_lbl.configure(text="Syncing...", text_color=Theme.WARNING)
        elif status == STATUS_ERROR:
            self.status_dot.configure(text_color=Theme.DANGER)
            self.status_lbl.configure(text="Sync Error", text_color=Theme.DANGER)
        else: # Offline
            self.status_dot.configure(text_color=Theme.TEXT_MUTED)
            self.status_lbl.configure(text="Offline", text_color=Theme.TEXT_MUTED)

