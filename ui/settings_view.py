"""Settings and configuration screen for NudgeDesk."""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable, Optional

from config.theme import Theme, PALETTES, Palette
from config.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION, CREDENTIALS_FILE_PATH
from utils.config_manager import config_manager
from utils.windows_startup import set_start_with_windows, is_start_with_windows_enabled
from services.google_auth import google_auth
from database.db_manager import db
from utils.logger import logger

class ThemePaletteCard(ctk.CTkFrame):
    """Card displaying a curated theme palette with preview swatches and mode badge."""

    def __init__(self, master, palette: Palette, is_active: bool, on_select: Callable[[str], None], **kwargs):
        border_c = palette.accent if is_active else Theme.BORDER
        border_w = 2 if is_active else 1

        super().__init__(
            master,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=border_w,
            border_color=border_c,
            **kwargs
        )
        self.palette = palette
        self.is_active = is_active
        self.on_select = on_select

        self._build_ui()

    def _build_ui(self) -> None:
        # Top row: Icon + Name + Subtitle + Badge
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(12, 6))

        # Icon box
        icon_box = ctk.CTkFrame(
            top_row,
            width=32,
            height=32,
            corner_radius=16,
            fg_color=self.palette.bg_main,
            border_width=1,
            border_color=self.palette.border
        )
        icon_box.pack(side="left", padx=(0, 8))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=self.palette.accent_icon, font=Theme.get_font(13)).pack(expand=True)

        # Title & Subtitle
        title_box = ctk.CTkFrame(top_row, fg_color="transparent")
        title_box.pack(side="left", fill="y", expand=True)

        ctk.CTkLabel(
            title_box,
            text=self.palette.name,
            font=Theme.get_font(13, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text=self.palette.subtitle,
            font=Theme.get_font(10),
            text_color=self.palette.accent if self.is_active else Theme.TEXT_SECONDARY,
            anchor="w"
        ).pack(anchor="w")

        # Badge: LIGHT THEME or DARK THEME
        badge_bg = self.palette.accent
        badge_text_color = self.palette.accent_text
        badge_label = "☀️ LIGHT THEME" if self.palette.is_light else ("⚡ DARK THEME" if self.palette.id == "zest" else "🌙 DARK THEME")

        badge_frame = ctk.CTkFrame(top_row, fg_color=badge_bg, corner_radius=12)
        badge_frame.pack(side="right")
        ctk.CTkLabel(
            badge_frame,
            text=badge_label,
            font=Theme.get_font(9, "bold"),
            text_color=badge_text_color
        ).pack(padx=8, pady=3)

        # Description
        ctk.CTkLabel(
            self,
            text=self.palette.description,
            font=Theme.get_font(11),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=340,
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=14, pady=(0, 10))

        # Color Swatch Tags row
        tags_row = ctk.CTkFrame(self, fg_color="transparent")
        tags_row.pack(fill="x", padx=14, pady=(0, 12))

        for label, tag_bg, tag_text_color in self.palette.tags:
            has_border = tag_bg in ("#FFFFFF", "#FAF6EF", "#F2FAF5", "#F0F7FB")
            tag_frame = ctk.CTkFrame(
                tags_row,
                fg_color=tag_bg,
                corner_radius=6,
                border_width=1 if has_border else 0,
                border_color=self.palette.border if has_border else None
            )
            tag_frame.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                tag_frame,
                text=label,
                font=Theme.get_font(10, "bold"),
                text_color=tag_text_color
            ).pack(padx=8, pady=2)

        # Click handler bindings
        self._bind_click(self)

    def _bind_click(self, widget) -> None:
        widget.bind("<Button-1>", lambda e: self.on_select(self.palette.id))
        for child in widget.winfo_children():
            self._bind_click(child)

class SettingsView(ctk.CTkFrame):
    """Full-featured modern settings panel."""

    def __init__(
        self,
        master,
        on_close: Callable[[], None],
        on_sync_now: Callable[[], None],
        on_auth_trigger: Callable[[Optional[Path]], None],
        on_theme_changed: Callable[[str], None],
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_close = on_close
        self.on_sync_now = on_sync_now
        self.on_auth_trigger = on_auth_trigger
        self.on_theme_changed = on_theme_changed

        self._build_ui()

    def _build_ui(self) -> None:
        # Title bar
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.pack(fill="x", padx=24, pady=(16, 12))

        ctk.CTkLabel(
            title_bar,
            text="Settings",
            font=Theme.get_font(20, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        back_btn = ctk.CTkButton(
            title_bar,
            text="← Back to Tasks",
            font=Theme.get_font(12, "bold"),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            border_width=1,
            border_color=Theme.BORDER,
            height=32,
            width=120,
            corner_radius=8,
            command=self.on_close
        )
        back_btn.pack(side="right")

        # Scrollable Settings Form
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.BG_CARD_HOVER
        )
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # -------------------------------------------------------------
        # Section 1: Google Account Integration
        # -------------------------------------------------------------
        self._build_account_section(scroll)

        # -------------------------------------------------------------
        # Section 2: Synchronization Preferences
        # -------------------------------------------------------------
        self._build_sync_section(scroll)

        # -------------------------------------------------------------
        # Section 3: Windows Desktop Preferences
        # -------------------------------------------------------------
        self._build_windows_section(scroll)

        # -------------------------------------------------------------
        # Section 4: Appearance & Theme
        # -------------------------------------------------------------
        self._build_appearance_section(scroll)

        # -------------------------------------------------------------
        # Section 5: Maintenance & About
        # -------------------------------------------------------------
        self._build_about_section(scroll)

    def _build_card(self, parent, title: str) -> ctk.CTkFrame:
        """Helper to create a Bento Box card container."""
        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER
        )
        card.pack(fill="x", pady=8)

        ctk.CTkLabel(
            card,
            text=title,
            font=Theme.get_font(14, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=18, pady=(16, 10))

        return card

    def _build_account_section(self, parent) -> None:
        card = self._build_card(parent, "Google Tasks Integration")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 14))

        # Status & Account details
        info_col = ctk.CTkFrame(row, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        email = config_manager.get("account_email")
        self.account_status_lbl = ctk.CTkLabel(
            info_col,
            text=f"Connected as {email}" if email else "Not connected to Google Tasks",
            font=Theme.get_font(13, "bold"),
            text_color=Theme.SUCCESS if email else Theme.TEXT_MUTED,
            anchor="w"
        )
        self.account_status_lbl.pack(anchor="w")

        hint_text = "OAuth 2.0 with official Google Tasks API v1."
        ctk.CTkLabel(
            info_col,
            text=hint_text,
            font=Theme.get_font(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        # Action Buttons
        btn_box = ctk.CTkFrame(row, fg_color="transparent")
        btn_box.pack(side="right")

        self.import_creds_btn = ctk.CTkButton(
            btn_box,
            text="Load credentials.json",
            font=Theme.get_font(12),
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            height=34,
            corner_radius=8,
            command=self._handle_import_credentials
        )
        self.import_creds_btn.pack(side="left", padx=(0, 8))

        self.sign_in_btn = ctk.CTkButton(
            btn_box,
            text="Sign Out" if email else "Sign In with Google",
            font=Theme.get_font(12, "bold"),
            fg_color=Theme.DANGER if email else Theme.ACCENT,
            hover_color="#DC2626" if email else Theme.ACCENT_HOVER,
            text_color="#FFFFFF" if email else ("#111827", "#111827"),
            height=34,
            corner_radius=8,
            command=self._handle_auth_toggle
        )
        self.sign_in_btn.pack(side="left")

    def _build_sync_section(self, parent) -> None:
        card = self._build_card(parent, "Synchronization")

        # Auto-sync switch
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=18, pady=(0, 10))

        ctk.CTkLabel(
            row1,
            text="Automatic Background Synchronization",
            font=Theme.get_font(13),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        self.auto_sync_var = ctk.BooleanVar(value=config_manager.get("auto_sync", True))
        auto_switch = ctk.CTkSwitch(
            row1,
            text="",
            variable=self.auto_sync_var,
            progress_color=Theme.ACCENT,
            command=lambda: config_manager.set("auto_sync", self.auto_sync_var.get())
        )
        auto_switch.pack(side="right")

        # Sync interval dropdown
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=18, pady=(0, 16))

        ctk.CTkLabel(
            row2,
            text="Sync Interval",
            font=Theme.get_font(13),
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left")

        interval_map = {
            "1 Minute": 60,
            "2 Minutes": 120,
            "5 Minutes (Default)": 300,
            "10 Minutes": 600,
            "15 Minutes": 900,
            "30 Minutes": 1800,
            "1 Hour": 3600,
        }
        current_val = config_manager.get("sync_interval", 300)
        selected_label = "5 Minutes (Default)"
        for k, v in interval_map.items():
            if v == current_val:
                selected_label = k
                break

        def _on_interval_select(chosen_label):
            sec = interval_map.get(chosen_label, 300)
            config_manager.set("sync_interval", sec)

        interval_menu = ctk.CTkOptionMenu(
            row2,
            values=list(interval_map.keys()),
            font=Theme.get_font(12),
            fg_color=Theme.BG_INPUT,
            button_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            height=32,
            corner_radius=8,
            command=_on_interval_select
        )
        interval_menu.set(selected_label)
        interval_menu.pack(side="right")

    def _build_windows_section(self, parent) -> None:
        card = self._build_card(parent, "Windows 11 Integration")

        # Start with Windows
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(row1, text="Start with Windows", font=Theme.get_font(13), text_color=Theme.TEXT_PRIMARY).pack(side="left")

        is_startup = is_start_with_windows_enabled()
        self.startup_var = ctk.BooleanVar(value=is_startup)
        ctk.CTkSwitch(
            row1,
            text="",
            variable=self.startup_var,
            progress_color=Theme.ACCENT,
            command=self._handle_startup_toggle
        ).pack(side="right")

        # Minimize to Tray
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(row2, text="Minimize to System Tray on Close", font=Theme.get_font(13), text_color=Theme.TEXT_PRIMARY).pack(side="left")

        self.tray_var = ctk.BooleanVar(value=config_manager.get("minimize_to_tray", True))
        ctk.CTkSwitch(
            row2,
            text="",
            variable=self.tray_var,
            progress_color=Theme.ACCENT,
            command=lambda: config_manager.set("minimize_to_tray", self.tray_var.get())
        ).pack(side="right")

        # Launch Minimized
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(row3, text="Launch Minimized to System Tray", font=Theme.get_font(13), text_color=Theme.TEXT_PRIMARY).pack(side="left")

        self.launch_min_var = ctk.BooleanVar(value=config_manager.get("launch_minimized", False))
        ctk.CTkSwitch(
            row3,
            text="",
            variable=self.launch_min_var,
            progress_color=Theme.ACCENT,
            command=lambda: config_manager.set("launch_minimized", self.launch_min_var.get())
        ).pack(side="right")

        # Windows Notifications
        row4 = ctk.CTkFrame(card, fg_color="transparent")
        row4.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkLabel(row4, text="Windows Toast Notifications for Due Tasks", font=Theme.get_font(13), text_color=Theme.TEXT_PRIMARY).pack(side="left")

        self.notif_var = ctk.BooleanVar(value=config_manager.get("notifications_enabled", True))
        ctk.CTkSwitch(
            row4,
            text="",
            variable=self.notif_var,
            progress_color=Theme.ACCENT,
            command=lambda: config_manager.set("notifications_enabled", self.notif_var.get())
        ).pack(side="right")

    def _build_appearance_section(self, parent) -> None:
        card = self._build_card(parent, "🎨  Theme Palettes")

        subtitle = "Switch between curated color palettes. Your theme is automatically saved to your user profile and syncs across all devices."
        ctk.CTkLabel(
            card,
            text=subtitle,
            font=Theme.get_font(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            wraplength=760,
            justify="left"
        ).pack(fill="x", padx=18, pady=(0, 14))

        # Grid of 2 columns
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(0, 16))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        active_palette_id = config_manager.get("theme_palette", "zest")

        # Layout matching user's earlier project screenshot
        layout = [
            ("warm_linen", 0, 0),
            ("emerald_pure", 0, 1),
            ("nordic_frost", 1, 0),
            ("zest", 1, 1),
            ("slate_pro", 2, 0),
            ("midnight_oled", 2, 1),
        ]

        self.palette_cards = {}
        for pal_id, r, c in layout:
            pal = PALETTES.get(pal_id)
            if not pal:
                continue
            is_active = (pal_id == active_palette_id)
            p_card = ThemePaletteCard(
                grid,
                palette=pal,
                is_active=is_active,
                on_select=self._handle_palette_select
            )
            padx = (0, 8) if c == 0 else (8, 0)
            p_card.grid(row=r, column=c, padx=padx, pady=6, sticky="nsew")
            self.palette_cards[pal_id] = p_card

    def _handle_palette_select(self, palette_id: str) -> None:
        config_manager.set("theme_palette", palette_id)
        self.on_theme_changed(palette_id)

    def _build_about_section(self, parent) -> None:
        card = self._build_card(parent, "Data & About")

        # Clear Cache Button
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(row1, text="Clear Local SQLite Cache", font=Theme.get_font(13), text_color=Theme.TEXT_PRIMARY).pack(side="left")

        ctk.CTkButton(
            row1,
            text="Clear Cache",
            font=Theme.get_font(12),
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.DANGER,
            text_color=Theme.TEXT_SECONDARY,
            height=32,
            width=100,
            corner_radius=8,
            command=self._handle_clear_cache
        ).pack(side="right")

        # About info
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=18, pady=(0, 14))

        about_text = f"{APP_NAME} v{APP_VERSION} – {APP_DESCRIPTION}"
        ctk.CTkLabel(
            row2,
            text=about_text,
            font=Theme.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

    def _handle_startup_toggle(self) -> None:
        enable = self.startup_var.get()
        set_start_with_windows(enable)
        config_manager.set("start_with_windows", enable)

    def _handle_import_credentials(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Select Google OAuth credentials.json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                dest = CREDENTIALS_FILE_PATH
                dest.write_text(Path(filepath).read_text(encoding="utf-8"), encoding="utf-8")
                messagebox.showinfo("Credentials Loaded", f"credentials.json imported successfully!\nSaved to: {dest}")
                self.on_auth_trigger(dest)
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import credentials file: {e}")

    def _handle_auth_toggle(self) -> None:
        email = config_manager.get("account_email")
        if email:
            if messagebox.askyesno("Sign Out", "Are you sure you want to sign out from Google Tasks?"):
                google_auth.sign_out()
                self.account_status_lbl.configure(text="Not connected to Google Tasks", text_color=Theme.TEXT_MUTED)
                self.sign_in_btn.configure(text="Sign In with Google", fg_color=Theme.ACCENT, text_color=("#111827", "#111827"))
        else:
            self.on_auth_trigger(None)

    def refresh_state(self) -> None:
        email = config_manager.get("account_email")
        if email:
            self.account_status_lbl.configure(text=f"Connected as {email}", text_color=Theme.SUCCESS)
            self.sign_in_btn.configure(text="Sign Out", fg_color=Theme.DANGER, text_color="#FFFFFF")
        else:
            self.account_status_lbl.configure(text="Not connected to Google Tasks", text_color=Theme.TEXT_MUTED)
            self.sign_in_btn.configure(text="Sign In with Google", fg_color=Theme.ACCENT, text_color=("#111827", "#111827"))

    def _handle_clear_cache(self) -> None:
        if messagebox.askyesno("Clear Cache", "Clear all cached local tasks? They will be re-downloaded upon the next sync."):
            db.clear_all_data()
            self.on_sync_now()
            messagebox.showinfo("Cache Cleared", "Local task cache has been cleared.")

