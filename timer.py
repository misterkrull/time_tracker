import time
import tkinter as tk
from tkinter import ttk

from common_functions import duration_to_string, time_decorator
from subsession import Subsession

TK_BUTTON_STATES = {True: "normal", False: "disabled"}


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
                is_same_activity = self.activity_number == other_timer.activity_number
                self.is_running = is_same_activity
                self.gui_start_button.config(state=TK_BUTTON_STATES[not is_same_activity])
                return

    @time_decorator
    def _start_timer(self) -> None:
        """
        Запускается при нажатии на кнопку "Старт <timer.id>"
        """
        if self.is_running:
            for timer in self._gui_layer.timer_list:
                timer.gui_combobox.config(state="readonly")
                timer.gui_label.config(bg=self._gui_layer.DEFAULT_WIN_COLOR)
            self.gui_combobox.config(state="disable")
            self.gui_label.config(bg="green")
            return

        was_timecounter_running: bool = False
        if self._gui_layer.time_counter.is_running():
            was_timecounter_running = True
            self._gui_layer.time_counter.stop()
        self._gui_layer.time_counter.start()
        current_time = time.time()
        
        self._gui_layer.app.current_activity = self.activity_number
        
        for timer in self._gui_layer.timer_list:
            if timer.activity_number == self.activity_number:
                timer.is_running = True
            else:
                timer.is_running = False
            timer.gui_combobox.config(state="readonly")
            timer.gui_label.config(bg=self._gui_layer.DEFAULT_WIN_COLOR)

        self.gui_combobox.config(state="disable")
        self.gui_label.config(bg="green")

        if was_timecounter_running:
            self._gui_layer.subsession.ending(current_time)

        self._gui_layer.subsession = Subsession(current_time, self._gui_layer.app)
