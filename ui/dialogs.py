"""Dialogs for Task Creation, Editing, Confirmation, and Account Setup."""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from datetime import date, datetime
from typing import Optional, Callable, Dict, Any, List

from config.theme import Theme
from config.constants import PRIORITY_NONE, PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_LABELS
from database.models import Task, TaskList
from database.db_manager import db
from utils.logger import logger

class BaseDialog(ctk.CTkToplevel):
    """Base modal dialog with Windows 11 rounded appearance and key bindings."""

    def __init__(self, parent, title: str, width: int = 460, height: int = 420):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_MAIN)
        
        # Center dialog relative to parent
        self.transient(parent)
        self.grab_set()
        
        # Calculate center coordinates
        try:
            parent.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_x()
            py = parent.winfo_y()
            x = px + (pw - width) // 2
            y = py + (ph - height) // 2
            self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.bind("<Escape>", lambda e: self.destroy())


class TaskDialog(BaseDialog):
    """Dialog for creating or editing tasks."""

    def __init__(self, parent, task: Optional[Task] = None, default_list_id: Optional[str] = None, on_save: Optional[Callable[[Dict[str, Any]], None]] = None):
        is_edit = task is not None
        super().__init__(parent, "Edit Task" if is_edit else "Create New Task", width=480, height=520)
        
        self.task = task
        self.on_save = on_save
        self.lists = db.get_all_lists()

        # Container frame
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Title Label
        title_lbl = ctk.CTkLabel(
            container,
            text="Edit Task" if is_edit else "Add New Task",
            font=Theme.get_font(18, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w", padx=20, pady=(18, 12))

        # Task Title Input
        ctk.CTkLabel(container, text="Title *", font=Theme.get_font(12, "bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(4, 2))
        self.title_entry = ctk.CTkEntry(
            container,
            placeholder_text="What do you want to accomplish?",
            font=Theme.get_font(13),
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER,
            height=38,
            corner_radius=8
        )
        self.title_entry.pack(fill="x", padx=20, pady=(0, 10))
        if task:
            self.title_entry.insert(0, task.title)
        self.title_entry.focus_set()

        # Task Description / Notes
        ctk.CTkLabel(container, text="Notes / Description (Optional)", font=Theme.get_font(12, "bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(4, 2))
        self.notes_textbox = ctk.CTkTextbox(
            container,
            font=Theme.get_font(12),
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER,
            border_width=1,
            height=75,
            corner_radius=8
        )
        self.notes_textbox.pack(fill="x", padx=20, pady=(0, 10))
        if task and task.notes:
            self.notes_textbox.insert("1.0", task.notes)

        # Due Date & Priority row
        row_frame = ctk.CTkFrame(container, fg_color="transparent")
        row_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Due Date
        due_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        due_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(due_col, text="Due Date (YYYY-MM-DD)", font=Theme.get_font(12, "bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", pady=(0, 2))
        self.due_entry = ctk.CTkEntry(
            due_col,
            placeholder_text=date.today().isoformat(),
            font=Theme.get_font(13),
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER,
            height=36,
            corner_radius=8
        )
        self.due_entry.pack(fill="x")
        if task and task.due:
            self.due_entry.insert(0, task.due)

        # Priority selector
        prio_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        prio_col.pack(side="right", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(prio_col, text="Priority (Local)", font=Theme.get_font(12, "bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", pady=(0, 2))
        self.prio_var = ctk.StringVar(value=PRIORITY_LABELS.get(task.priority if task else 0, "None"))
        self.prio_menu = ctk.CTkOptionMenu(
            prio_col,
            variable=self.prio_var,
            values=["None", "Low", "Medium", "High"],
            fg_color=Theme.BG_INPUT,
            button_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            height=36,
            corner_radius=8
        )
        self.prio_menu.pack(fill="x")

        # Task List Selector
        ctk.CTkLabel(container, text="Task List", font=Theme.get_font(12, "bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(4, 2))
        
        list_options = [lst.title for lst in self.lists] if self.lists else ["Default List"]
        self.list_map = {lst.title: lst.id for lst in self.lists} if self.lists else {"Default List": "@default"}
        
        # Find default selection
        selected_list_title = list_options[0]
        if task:
            for lst in self.lists:
                if lst.id == task.list_id or lst.remote_id == task.list_id:
                    selected_list_title = lst.title
                    break
        elif default_list_id:
            for lst in self.lists:
                if lst.id == default_list_id or lst.remote_id == default_list_id:
                    selected_list_title = lst.title
                    break

        self.list_var = ctk.StringVar(value=selected_list_title)
        self.list_menu = ctk.CTkOptionMenu(
            container,
            variable=self.list_var,
            values=list_options,
            fg_color=Theme.BG_INPUT,
            button_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            height=36,
            corner_radius=8
        )
        self.list_menu.pack(fill="x", padx=20, pady=(0, 16))

        # Bottom Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(8, 14), side="bottom")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=Theme.get_font(13),
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            height=36,
            width=90,
            command=self.destroy
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Task" if is_edit else "Create Task",
            font=Theme.get_font(13, "bold"),
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color=("#111827", "#111827"),
            height=36,
            width=120,
            command=self._handle_save
        )
        save_btn.pack(side="right")

        # Pressing Enter in title saves immediately
        self.title_entry.bind("<Return>", lambda e: self._handle_save())

    def _handle_save(self) -> None:
        title = self.title_entry.get().strip()
        if not title:
            self.title_entry.configure(border_color="#EF4444")
            return

        notes = self.notes_textbox.get("1.0", "end-1c").strip()
        due = self.due_entry.get().strip()
        if due:
            # Validate simple date format YYYY-MM-DD
            try:
                datetime.strptime(due[:10], "%Y-%m-%d")
                due = due[:10]
            except ValueError:
                self.due_entry.configure(border_color="#EF4444")
                return
        else:
            due = None

        prio_label = self.prio_var.get()
        prio_map = {"None": PRIORITY_NONE, "Low": PRIORITY_LOW, "Medium": PRIORITY_MEDIUM, "High": PRIORITY_HIGH}
        priority = prio_map.get(prio_label, PRIORITY_NONE)

        chosen_title = self.list_var.get()
        list_id = self.list_map.get(chosen_title, "@default")

        data = {
            "title": title,
            "notes": notes,
            "due": due,
            "priority": priority,
            "list_id": list_id
        }

        if self.on_save:
            self.on_save(data)
        self.destroy()


class NewListDialog(BaseDialog):
    """Dialog to create a new task list."""

    def __init__(self, parent, on_create: Optional[Callable[[str], None]] = None):
        super().__init__(parent, "New Task List", width=380, height=210)
        self.on_create = on_create

        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(container, text="Create Task List", font=Theme.get_font(16, "bold"), text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(16, 8))

        self.name_entry = ctk.CTkEntry(
            container,
            placeholder_text="List name (e.g. Work, Personal)",
            font=Theme.get_font(13),
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER,
            height=36,
            corner_radius=8
        )
        self.name_entry.pack(fill="x", padx=18, pady=(0, 16))
        self.name_entry.focus_set()

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, side="bottom", pady=(0, 14))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            width=80,
            height=34,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Create",
            font=Theme.get_font(13, "bold"),
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color=("#111827", "#111827"),
            width=100,
            height=34,
            command=self._handle_create
        ).pack(side="right")

        self.name_entry.bind("<Return>", lambda e: self._handle_create())

    def _handle_create(self) -> None:
        name = self.name_entry.get().strip()
        if name and self.on_create:
            self.on_create(name)
        self.destroy()


class ConfirmDeleteDialog(BaseDialog):
    """Confirmation modal before deleting tasks or lists."""

    def __init__(self, parent, item_name: str, item_type: str = "task", on_confirm: Optional[Callable[[], None]] = None):
        super().__init__(parent, f"Delete {item_type.capitalize()}?", width=380, height=190)
        self.on_confirm = on_confirm

        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(container, text=f"Delete this {item_type}?", font=Theme.get_font(16, "bold"), text_color=Theme.DANGER).pack(anchor="w", padx=18, pady=(16, 6))

        msg = f"Are you sure you want to delete \"{item_name}\"? This action cannot be undone."
        ctk.CTkLabel(container, text=msg, font=Theme.get_font(12), text_color=Theme.TEXT_SECONDARY, wraplength=320, justify="left").pack(anchor="w", padx=18, pady=(0, 16))

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, side="bottom", pady=(0, 14))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            width=80,
            height=34,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Delete",
            font=Theme.get_font(13, "bold"),
            fg_color=Theme.DANGER,
            hover_color="#DC2626",
            text_color="#FFFFFF",
            width=90,
            height=34,
            command=self._handle_delete
        ).pack(side="right")

    def _handle_delete(self) -> None:
        if self.on_confirm:
            self.on_confirm()
        self.destroy()

