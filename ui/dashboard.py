"""Dashboard header and Bento Box metrics cards."""

import customtkinter as ctk
from datetime import datetime
from typing import Callable, Dict, Any, Optional

from config.theme import Theme
from utils.config_manager import config_manager

class BentoCard(ctk.CTkFrame):
    """Clickable Bento Box metric tile."""

    def __init__(self, master, title: str, count: int, icon: str, accent_color: tuple, on_click: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(
            master,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs
        )
        self.on_click = on_click
        self.accent_color = accent_color

        # Card inner layout
        self.pack_propagate(False)

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(14, 2))

        self.title_lbl = ctk.CTkLabel(
            top_row,
            text=title,
            font=Theme.get_font(12, "bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.title_lbl.pack(side="left")

        self.icon_lbl = ctk.CTkLabel(
            top_row,
            text=icon,
            font=Theme.get_font(14)
        )
        self.icon_lbl.pack(side="right")

        self.count_lbl = ctk.CTkLabel(
            self,
            text=str(count),
            font=Theme.get_font(28, "bold"),
            text_color=self.accent_color
        )
        self.count_lbl.pack(anchor="w", padx=16, pady=(2, 10))

        # Hover and click interactions
        for widget in (self, top_row, self.title_lbl, self.icon_lbl, self.count_lbl):
            widget.bind("<Enter>", lambda e: self._on_hover(True))
            widget.bind("<Leave>", lambda e: self._on_hover(False))
            if on_click:
                widget.bind("<Button-1>", lambda e: on_click())

    def _on_hover(self, hovering: bool) -> None:
        if hovering:
            self.configure(border_color=self.accent_color)
        else:
            self.configure(border_color=Theme.BORDER)

    def set_count(self, count: int) -> None:
        self.count_lbl.configure(text=str(count))


class Dashboard(ctk.CTkFrame):
    """Dashboard header and Bento metrics for the main application area."""

    def __init__(
        self,
        master,
        on_add_task: Callable[[], None],
        on_sync_now: Callable[[], None],
        on_search: Callable[[str], None],
        on_card_click: Callable[[str], None],
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_add_task = on_add_task
        self.on_sync_now = on_sync_now
        self.on_search = on_search
        self.on_card_click = on_card_click

        self._build_header()
        self._build_bento_cards()

    def _get_greeting(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"

    def _build_header(self) -> None:
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(16, 12))

        # Left: Greeting & Current Date
        left_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_box.pack(side="left")

        user_name = config_manager.get("account_name")
        greeting_text = self._get_greeting()
        if user_name:
            greeting_text += f", {user_name.split()[0]}"
        else:
            greeting_text += "!"

        self.greeting_lbl = ctk.CTkLabel(
            left_box,
            text=greeting_text,
            font=Theme.get_font(22, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.greeting_lbl.pack(anchor="w")

        today_str = datetime.now().strftime("%A, %B %d, %Y")
        self.date_lbl = ctk.CTkLabel(
            left_box,
            text=today_str,
            font=Theme.get_font(12),
            text_color=Theme.TEXT_SECONDARY
        )
        self.date_lbl.pack(anchor="w", pady=(1, 0))

        # Right: Search & Actions
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right")

        # Search Box
        self.search_entry = ctk.CTkEntry(
            right_box,
            placeholder_text="🔍 Search tasks...",
            font=Theme.get_font(12),
            fg_color=Theme.BG_CARD,
            border_color=Theme.BORDER,
            width=200,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search(self.search_entry.get()))

        # Sync Now Button
        self.sync_btn = ctk.CTkButton(
            right_box,
            text="🔄 Sync",
            font=Theme.get_font(12, "bold"),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER,
            height=36,
            width=80,
            corner_radius=8,
            command=self.on_sync_now
        )
        self.sync_btn.pack(side="left", padx=(0, 10))

        # Add Task Button (Accent Gold)
        self.add_btn = ctk.CTkButton(
            right_box,
            text="+ Add Task",
            font=Theme.get_font(13, "bold"),
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color=("#111827", "#111827"),
            height=36,
            width=105,
            corner_radius=8,
            command=self.on_add_task
        )
        self.add_btn.pack(side="left")

    def _build_bento_cards(self) -> None:
        """Bento Box 4-card metric strip."""
        cards_grid = ctk.CTkFrame(self, fg_color="transparent")
        cards_grid.pack(fill="x", padx=24, pady=(0, 16))
        cards_grid.columnconfigure((0, 1, 2, 3), weight=1, uniform="bento")

        self.today_card = BentoCard(
            cards_grid,
            title="Today's Tasks",
            count=0,
            icon="☀️",
            accent_color=Theme.ACCENT,
            on_click=lambda: self.on_card_click("my_day"),
            height=90
        )
        self.today_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self.upcoming_card = BentoCard(
            cards_grid,
            title="Upcoming",
            count=0,
            icon="📅",
            accent_color=Theme.INFO,
            on_click=lambda: self.on_card_click("upcoming"),
            height=90
        )
        self.upcoming_card.grid(row=0, column=1, padx=4, sticky="nsew")

        self.completed_card = BentoCard(
            cards_grid,
            title="Completed",
            count=0,
            icon="✅",
            accent_color=Theme.SUCCESS,
            on_click=lambda: self.on_card_click("completed"),
            height=90
        )
        self.completed_card.grid(row=0, column=2, padx=4, sticky="nsew")

        self.pending_card = BentoCard(
            cards_grid,
            title="Total Pending",
            count=0,
            icon="⏳",
            accent_color=Theme.WARNING,
            on_click=lambda: self.on_card_click("all"),
            height=90
        )
        self.pending_card.grid(row=0, column=3, padx=(8, 0), sticky="nsew")

    def update_metrics(self, counts: Dict[str, int]) -> None:
        self.today_card.set_count(counts.get("today", 0))
        self.upcoming_card.set_count(counts.get("upcoming", 0))
        self.completed_card.set_count(counts.get("completed", 0))
        self.pending_card.set_count(counts.get("pending", 0))

        # Update greeting if name changed
        user_name = config_manager.get("account_name")
        greeting_text = self._get_greeting()
        if user_name:
            greeting_text += f", {user_name.split()[0]}"
        else:
            greeting_text += "!"
        self.greeting_lbl.configure(text=greeting_text)

