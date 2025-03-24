import tkinter as tk
from tkinter import ttk
from typing import Callable

from common_functions import duration_to_string
from gui.gui_constants import (
    TK_BUTTON_STATES,
    TK_COMBOBOX_STATE,
    TK_IS_GREEN_COLORED,
)


class TimerFrame:
    def __init__(
        self,
        id: int,
        activity_id: int,
        activity_table: dict[int, str],
        duration_table: dict[int, int],
        main_frame: tk.Frame,
        on_start_button: Callable[[int], None],
        is_session_active: bool
    ):
        self.id = id
        self.activity_id = activity_id
        self._activity_table = activity_table
        self._duration_table = duration_table
        self._on_start_button = on_start_button
        self._is_session_active = is_session_active

        self._time_counter_duration: int = 0
        self._current_activity_id: int | None = None
        self._is_master = False

        self._init_widgets(main_frame)

    def _get_activity_text(self, activity_id: int) -> str:
        return f"{activity_id}. {self._activity_table[activity_id]}"

    def _init_widgets(self, main_frame: tk.Frame) -> None:
        timer_frame = tk.Frame(main_frame)
        timer_frame.pack(side=tk.LEFT, padx=10)

        # Лейбл
        self._gui_label = tk.Label(
            timer_frame,
            text=duration_to_string(self._duration_table[self.activity_id]),
            font=("Helvetica", 36),
        )
        self._gui_label.pack()

        # Комбобокс
        # StringVar нужен для связи со значением комбобокса
        self._combobox_variable = tk.StringVar()
        self._combobox_variable.set(self._get_activity_text(self.activity_id))
        self._gui_combobox = ttk.Combobox(
            timer_frame,
            textvariable=self._combobox_variable,
            values=[self._get_activity_text(id) for id in self._activity_table.keys()],
            state="readonly",
        )
        self._gui_combobox.pack(pady=5)
        self._gui_combobox.bind("<<ComboboxSelected>>", self._select_activity)

        # Кнопка "Старт <timer_number>"
        self.gui_start_button = tk.Button(
            timer_frame,
            text=f"Старт {self.id + 1}",
            command=lambda: self._on_start_button(self.id),
            font=("Helvetica", 14),
            width=10,
            height=1,
            state=TK_BUTTON_STATES[self._is_session_active],
        )
        self.gui_start_button.pack(pady=5)

    def _select_activity(self, _: tk.Event):
        self.activity_id = list(self._activity_table.keys())[self._gui_combobox.current()]
        self._update_widgets_state()

    def _update_widgets_state(self):
        self._gui_label.config(bg=TK_IS_GREEN_COLORED[self._is_master])
        self._gui_combobox.config(
            state=TK_COMBOBOX_STATE[not self._is_master]
        )

        addition = self._time_counter_duration if self.activity_id == self._current_activity_id else 0
        self._gui_label.config(
            text=duration_to_string(self._duration_table[self.activity_id] + addition)
        )

    def setup_master(self, is_master: bool) -> None:
        self._is_master = is_master
        self._update_widgets_state()

    def reset(self, new_duration_table: dict[int, int]) -> None:
        self._is_master = False
        self._time_counter_duration = 0
        self._current_activity_id = None
        self.update_duration_table(new_duration_table)

    def update_duration_table(self, new_duration_table: dict[int, int]) -> None:
        self._duration_table = new_duration_table
        self._update_widgets_state()

    def update_time(self, time_counter_duration: int, current_activity_id: int) -> None:
        self._time_counter_duration = time_counter_duration
        self._current_activity_id = current_activity_id
        if self.activity_id == current_activity_id:
            self._update_widgets_state()
