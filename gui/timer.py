import tkinter as tk
from tkinter import ttk

from common_functions import duration_to_string, print_performance
from subsession import Subsession
from gui.gui_constants import TK_BUTTON_STATES, TK_COMBOBOX_STATE, TK_IS_GREEN_COLORED


class TimeTrackerTimer:
    def __init__(
        self,
        id: int,
        activity_number: int,
        gui_layer,
        main_frame: tk.Frame,
        timer_activity_names: dict[int, str],
    ):
        self.id = id
        self.activity_number = activity_number
        self.is_running: bool = False

        self._gui_layer = gui_layer
        self._timer_activity_names = timer_activity_names  # может заполнять этот список уже здесь?
        self._gui_init_combobox_value: tk.StringVar | None = None
        self.gui_label: tk.Label | None = None
        self.gui_combobox: ttk.Combobox | None = None
        self.gui_start_button: tk.Button | None = None

        self._init_gui_(main_frame)

    def _init_gui_(self, main_frame: tk.Frame) -> None:
        timer_frame = tk.Frame(main_frame)
        timer_frame.pack(side=tk.LEFT, padx=10)

        # Лейбл
        self.gui_label = tk.Label(
            timer_frame,
            text=duration_to_string(
                self._gui_layer.app.durations_of_activities_in_current_session[self.activity_number]
            ),
            font=("Helvetica", 36),
        )
        self.gui_label.pack()

        # Комбобокс
        self._gui_init_combobox_value = (
            tk.StringVar()
        )  # нужен для работы с выбранным значением комбобокса
        self._gui_init_combobox_value.set(self._timer_activity_names[self.activity_number])

        self.gui_combobox = ttk.Combobox(
            timer_frame,
            textvariable=self._gui_init_combobox_value,
            values=list(self._timer_activity_names.values()),
            state="readonly",
        )
        self.gui_combobox.pack(pady=5)
        self.gui_combobox.bind("<<ComboboxSelected>>", self._select_activity)

        # Кнопка "Старт <timer_number>"
        self.gui_start_button = tk.Button(
            timer_frame,
            text=f"Старт {self.id}",
            command=self._start_timer,
            font=("Helvetica", 14),
            width=10,
            height=1,
            state=TK_BUTTON_STATES[self._gui_layer.app.is_in_session],
        )
        self.gui_start_button.pack(pady=5)

    # TODO вернуть тут аннотацию
    # def _select_activity(self, _: tk.Event[ttk.Combobox]):
    def _select_activity(self, _):
        # Combobox считает с 0, а мы с 1
        self.activity_number = self.gui_combobox.current() + 1

        self.gui_label.config(
            text=duration_to_string(
                self._gui_layer.app.durations_of_activities_in_current_session[self.activity_number]
            )
        )

        for other_timer in self._gui_layer.timer_list:
            if other_timer.id == self.id:
                continue

            if other_timer.is_running:
                self.is_running = self.activity_number == other_timer.activity_number
                return

    @print_performance
    def _start_timer(self) -> None:
        """
        Запускается при нажатии на кнопку "Старт <timer.id>"
        """
        for timer in self._gui_layer.timer_list:
            is_timer_self: bool = timer.id == self.id
            timer.gui_combobox.config(state=TK_COMBOBOX_STATE[not is_timer_self])
            timer.gui_label.config(bg=TK_IS_GREEN_COLORED[is_timer_self])
            timer.gui_start_button.config(state=TK_BUTTON_STATES[not is_timer_self])

        if self.is_running:
            return

        was_timecounter_running: bool = False
        if self._gui_layer.time_counter.is_running():
            was_timecounter_running = True
            last_subsession_duration: int = self._gui_layer.time_counter.stop()

        current_time: int = self._gui_layer.time_counter.start()

        self._gui_layer.app.current_activity = self.activity_number
        for timer in self._gui_layer.timer_list:
            timer.is_running = timer.activity_number == self.activity_number

        if was_timecounter_running:
            # TODO подумать: может перенести его выше и избавиться от флага
            self._gui_layer.subsession.ending(last_subsession_duration)
        self._gui_layer.subsession = Subsession(current_time, self._gui_layer.app)
