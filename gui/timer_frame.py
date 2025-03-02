import tkinter as tk
from tkinter import ttk
from typing import Callable

from common_functions import duration_to_string
from session import Session, Activity
from gui.gui_constants import (
    BACKGROUND_COLOR,
    TK_BUTTON_STATES,
)


def _get_activity_text(activity: Activity) -> str:
    return f"{activity.id}. {activity.name}"


class TimerFrame:
    def __init__(
        self,
        id: int,
        activity_id: int,
        session: Session,
        activity_list: list[Activity],
        main_frame: tk.Frame,
        on_start_button: Callable[[int], None],
    ):
        self.id = id
        self.activity_id = activity_id

        self._session = session
        self._duration = self._session.get_activity_duration(self.activity_id)
        self._activity_table = {act.id: act for act in activity_list}
        self._on_start_button = on_start_button

        self._init_widgets(main_frame)

    def _init_widgets(self, main_frame: tk.Frame) -> None:
        timer_frame = tk.Frame(main_frame)
        timer_frame.pack(side=tk.LEFT, padx=10)

        # Лейбл
        self._gui_label = tk.Label(
            timer_frame,
            text=duration_to_string(self._duration),
            font=("Helvetica", 36),
        )
        self._gui_label.pack()

        # Комбобокс
        # StringVar нужен для связи со значением комбобокса
        self._combobox_variable = tk.StringVar()
        self._combobox_variable.set(_get_activity_text(self._activity_table[self.activity_id]))
        self._gui_combobox = ttk.Combobox(
            timer_frame,
            textvariable=self._combobox_variable,
            values=[_get_activity_text(act) for act in self._activity_table.values()],
            state="readonly",
        )
        self._gui_combobox.pack(pady=5)
        self._gui_combobox.bind("<<ComboboxSelected>>", self._select_activity)

        # Кнопка "Старт <timer_number>"
        self._gui_start_button = tk.Button(
            timer_frame,
            text=f"Старт {self.id + 1}",
            command=lambda: self._on_start_button(self.id),
            font=("Helvetica", 14),
            width=10,
            height=1,
            state=TK_BUTTON_STATES[self._session.is_active()],
        )
        self._gui_start_button.pack(pady=5)

    def _select_activity(self, _: tk.Event):
        self.activity_id = list(self._activity_table.keys())[self._gui_combobox.current()]
        self._duration = self._session.get_activity_duration(self.activity_id)
        self._gui_label.config(text=duration_to_string(self._duration))
        self._update_button_state()

    def stop(self) -> None:
        self._gui_combobox.config(state="readonly")
        self._gui_label.config(bg=BACKGROUND_COLOR)
        self._update_button_state()

    def start(self) -> None:
        self._gui_combobox.config(state="disabled")
        self._gui_label.config(bg="green")
        self._update_button_state()

    def is_active(self) -> bool:
        return self._session.subsessions[-1].activity.id == self.activity_id

    def update_time(self, time_counter_duration: int):
        self._gui_label.config(text=duration_to_string(self._duration + time_counter_duration))

    def _update_button_state(self):
        self._gui_start_button.config(state=TK_BUTTON_STATES[not self.is_active()])
