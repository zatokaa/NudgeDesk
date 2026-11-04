"""Task listing, task card items, and quick-add inline bar."""

import customtkinter as ctk
from datetime import date, datetime
from typing import Callable, List, Optional, Dict, Any

from config.theme import Theme
from config.constants import (
    PRIORITY_NONE, PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH,
    PRIORITY_LABELS, PRIORITY_COLORS
)
from database.models import Task, TaskList

class TaskCard(ctk.CTkFrame):
    """Modern Bento-styled Task item card."""

    def __init__(
        self,
        master,
        task: Task,
        list_name: str,
        on_toggle_complete: Callable[[Task], None],
        on_edit: Callable[[Task], None],
        on_delete: Callable[[Task], None],
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs
        )
        self.task = task
        self.list_name = list_name
        self.on_toggle_complete = on_toggle_complete
        self.on_edit = on_edit
        self.on_delete = on_delete

        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        # Left Column: Checkbox
        self.chk_var = ctk.BooleanVar(value=self.task.is_completed)
        self.checkbox = ctk.CTkCheckBox(
            inner,
            text="",
            variable=self.chk_var,
            width=22,
            height=22,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            border_width=2,
            border_color=Theme.BORDER,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            checkmark_color="#111827",
            command=lambda: self.on_toggle_complete(self.task)
        )
        self.checkbox.pack(side="left", padx=(0, 12))

        # Center Column: Title, Notes, Badges
        center = ctk.CTkFrame(inner, fg_color="transparent")
        center.pack(side="left", fill="both", expand=True)

        # Title
        title_color = Theme.TEXT_MUTED if self.task.is_completed else Theme.TEXT_PRIMARY
        self.title_lbl = ctk.CTkLabel(
            center,
            text=self.task.title,
            font=Theme.get_font(13, "bold"),
            text_color=title_color,
            anchor="w"
        )
        self.title_lbl.pack(fill="x")

        # Optional Notes preview
        if self.task.notes:
            notes_preview = self.task.notes.strip().replace("\n", " ")
            if len(notes_preview) > 90:
                notes_preview = notes_preview[:87] + "..."
            notes_lbl = ctk.CTkLabel(
                center,
                text=notes_preview,
                font=Theme.get_font(11),
                text_color=Theme.TEXT_SECONDARY,
                anchor="w"
            )
            notes_lbl.pack(fill="x", pady=(2, 0))

        # Badges row: Due Date, Category, Priority
        badges_frame = ctk.CTkFrame(center, fg_color="transparent")
        badges_frame.pack(fill="x", pady=(6, 0))

        # List category badge
        list_badge = ctk.CTkFrame(badges_frame, fg_color=Theme.BG_INPUT, corner_radius=5)
        list_badge.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            list_badge,
            text=f"📁 {self.list_name}",
            font=Theme.get_font(10),
            text_color=Theme.TEXT_SECONDARY
        ).pack(padx=6, pady=2)

        # Due date badge
        if self.task.due:
            today_str = date.today().isoformat()
            due_clean = self.task.due[:10]
            
            if self.task.is_completed:
                due_color = Theme.TEXT_MUTED
                due_bg = Theme.BG_INPUT
                due_text = f"📅 {due_clean}"
            elif due_clean < today_str:
                due_color = Theme.DANGER
                due_bg = ("#FEE2E2", "#3B1818")
                due_text = f"⚠️ Overdue ({due_clean})"
            elif due_clean == today_str:
                due_color = Theme.WARNING
                due_bg = ("#FEF3C7", "#362B14")
                due_text = "☀️ Today"
            else:
                due_color = Theme.INFO
                due_bg = ("#DBEAFE", "#152438")
                due_text = f"📅 {due_clean}"

            due_badge = ctk.CTkFrame(badges_frame, fg_color=due_bg, corner_radius=5)
            due_badge.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                due_badge,
                text=due_text,
                font=Theme.get_font(10, "bold"),
                text_color=due_color
            ).pack(padx=6, pady=2)

        # Priority badge
        if self.task.priority and self.task.priority > 0:
            p_label = PRIORITY_LABELS.get(self.task.priority, "None")
            p_color = PRIORITY_COLORS.get(self.task.priority, Theme.TEXT_MUTED)
            p_badge = ctk.CTkFrame(badges_frame, fg_color=Theme.BG_INPUT, corner_radius=5)
            p_badge.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                p_badge,
                text=f"🚩 {p_label}",
                font=Theme.get_font(10, "bold"),
                text_color=p_color
            ).pack(padx=6, pady=2)

        # Right Column: Quick Action buttons (Edit & Delete)
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right", padx=(8, 0))

        edit_btn = ctk.CTkButton(
            actions,
            text="✏️",
            width=28,
            height=28,
            font=Theme.get_font(12),
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=6,
            command=lambda: self.on_edit(self.task)
        )
        edit_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            actions,
            text="🗑️",
            width=28,
            height=28,
            font=Theme.get_font(12),
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=6,
            command=lambda: self.on_delete(self.task)
        )
        del_btn.pack(side="left", padx=2)


class TaskView(ctk.CTkFrame):
    """Container for the current task list view and quick-add bar."""

    def __init__(
        self,
        master,
        on_toggle_complete: Callable[[Task], None],
        on_edit_task: Callable[[Task], None],
        on_delete_task: Callable[[Task], None],
        on_quick_add: Callable[[str, Optional[str], Optional[str]], None],
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_toggle_complete = on_toggle_complete
        self.on_edit_task = on_edit_task
        self.on_delete_task = on_delete_task
        self.on_quick_add = on_quick_add

        self.current_title = "My Day"
        self._build_ui()

    def _build_ui(self) -> None:
        # View Title Bar
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.pack(fill="x", padx=24, pady=(4, 10))

        self.view_title_lbl = ctk.CTkLabel(
            title_bar,
            text="☀️ My Day",
            font=Theme.get_font(17, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.view_title_lbl.pack(side="left")

        self.task_count_lbl = ctk.CTkLabel(
            title_bar,
            text="0 tasks",
            font=Theme.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.task_count_lbl.pack(side="left", padx=(10, 0))

        # Inline Quick Add Bar
        self._build_quick_add_bar()

        # Scrollable Task List container
        self.tasks_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=Theme.BORDER,
            scrollbar_button_hover_color=Theme.BG_CARD_HOVER
        )
        self.tasks_scroll.pack(fill="both", expand=True, padx=24, pady=(10, 16))

    def _build_quick_add_bar(self) -> None:
        """Inline Bento quick-add input with Enter-to-save."""
        quick_frame = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER
        )
        quick_frame.pack(fill="x", padx=24, pady=(0, 4))

        inner = ctk.CTkFrame(quick_frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            inner,
            text="➕",
            font=Theme.get_font(13),
            text_color=Theme.ACCENT
        ).pack(side="left", padx=(4, 8))

        self.quick_input = ctk.CTkEntry(
            inner,
            placeholder_text="Quick add a task... (Press Enter to save)",
            font=Theme.get_font(13),
            fg_color="transparent",
            border_width=0,
            height=32
        )
        self.quick_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.quick_input.bind("<Return>", lambda e: self._handle_quick_submit())

        # Due Date Today Shortcut button
        self.today_shortcut_btn = ctk.CTkButton(
            inner,
            text="Due Today",
            width=75,
            height=28,
            font=Theme.get_font(11),
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=6,
            command=self._set_quick_due_today
        )
        self.today_shortcut_btn.pack(side="right", padx=(4, 0))
        self.quick_due_date = None

    def _set_quick_due_today(self) -> None:
        if self.quick_due_date:
            self.quick_due_date = None
            self.today_shortcut_btn.configure(text="Due Today", fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_SECONDARY)
        else:
            self.quick_due_date = date.today().isoformat()
            self.today_shortcut_btn.configure(text="☀️ Today", fg_color=Theme.ACCENT, text_color=("#111827", "#111827"))

    def _handle_quick_submit(self) -> None:
        title = self.quick_input.get().strip()
        if not title:
            return

        self.on_quick_add(title, None, self.quick_due_date)
        self.quick_input.delete(0, "end")
        self.quick_due_date = None
        self.today_shortcut_btn.configure(text="Due Today", fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_SECONDARY)

    def set_title(self, title: str) -> None:
        self.view_title_lbl.configure(text=title)

    def render_tasks(self, tasks: List[Task], list_map: Dict[str, str]) -> None:
        """Renders task cards or displays empty state."""
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()

        count = len(tasks)
        self.task_count_lbl.configure(text=f"{count} {'task' if count == 1 else 'tasks'}")

        if not tasks:
            # Empty state illustration
            empty_box = ctk.CTkFrame(self.tasks_scroll, fg_color="transparent")
            empty_box.pack(fill="both", expand=True, pady=60)

            ctk.CTkLabel(
                empty_box,
                text="🎉",
                font=Theme.get_font(36)
            ).pack(pady=(0, 8))

            ctk.CTkLabel(
                empty_box,
                text="All tasks completed!",
                font=Theme.get_font(16, "bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack()

            ctk.CTkLabel(
                empty_box,
                text="Enjoy your day, or quickly add a task above to get started.",
                font=Theme.get_font(12),
                text_color=Theme.TEXT_SECONDARY
            ).pack(pady=(4, 0))
            return

        for task in tasks:
            list_name = list_map.get(task.list_id, "Tasks")
            card = TaskCard(
                self.tasks_scroll,
                task=task,
                list_name=list_name,
                on_toggle_complete=self.on_toggle_complete,
                on_edit=self.on_edit_task,
                on_delete=self.on_delete_task
            )
            card.pack(fill="x", pady=4)

