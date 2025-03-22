# import keyboard
import time
import tkinter as tk

from common_functions import duration_to_string, print_performance, time_to_string
from gui.gui_constants import (
    MAIN_WINDOW_X, MAIN_WINDOW_Y,
    SESSION_BUTTON_DICT, SESSION_LABEL_DICT,
    TK_BUTTON_STATES,
)
from gui.manual_input_of_subsession import ManualInputOfSubsession
from gui.retroactively_termination_of_session import RetroactivelyTerminationOfSession
from gui.timer_frame import TimerFrame
from application_logic import ApplicationLogic
from time_counter import TimeCounter


class GuiLayer:
    def __init__(self, root: tk.Tk, app: ApplicationLogic):
        self.root = root
        self.app = app

        self.root.title("Мой трекер")
        self.root.geometry(f"{MAIN_WINDOW_X}x{MAIN_WINDOW_Y}")  # Устанавливаем размер окна
        self.root.resizable(False, False)  # Запрещаем изменение размеров
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)  # определяем метод закрытия окна
        self.DEFAULT_WIN_COLOR = self.root.cget("background")

        self.time_counter = TimeCounter(
            tk_root=self.root, on_tick_function=self.on_time_counter_tick
        )
        self._current_activity_id: int| None = None

        self._init_top_widgets()
        self._init_middle_widgets()
        self._init_bottom_widgets()

        # ГОРЯЧИЕ КЛАВИШИ -  имитируем нажатие нарисованных кнопок
        # keyboard.add_hotkey("Alt+F10", self.start_button[1].invoke)
        # keyboard.add_hotkey("Alt+F11", self.stop_button.invoke)
        # keyboard.add_hotkey("Alt+F12", self.start_button[2].invoke)

    def _init_top_widgets(self):
        """Создает фрейм верхней линии"""
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)

        # Создаем метку для текста "Сессия:"
        session_text_label = tk.Label(top_frame, text="Сессия:", font=("Helvetica", 14))
        session_text_label.pack(side=tk.LEFT)

        # Создаем метку для отображения номера текущей сессии
        self.current_session_number_label = tk.Label(
            top_frame,
            text=self.app.session.id if self.app.session.id is not None else "--",
            font=("Helvetica", 18)
        )
        self.current_session_number_label.pack(side=tk.LEFT, padx=10)  # Отступ между метками

        # Метка для текста "Началась:"/"Длилась:"
        self.session_label = tk.Label(
            top_frame, text=SESSION_LABEL_DICT[self.app.session.is_active()], font=("Helvetica", 14)
        )
        self.session_label.pack(side=tk.LEFT, padx=2)

        # Метка для времени начала сессии
        start_sess_datetime_label_text = (
            time_to_string(self.app.session.start_time)
            if self.app.session.is_active()
            else (
                duration_to_string(self.app.session.duration)
                if self.app.session.id is not None
                else "--:--:--"
            )
        )
        self.start_sess_datetime_label = tk.Label(
            top_frame,
            text=start_sess_datetime_label_text,
            font=("Helvetica", 14),
        )
        self.start_sess_datetime_label.pack(side=tk.LEFT, padx=2)

        # Кнопка "Новая сессия"/"Завершить сессию"
        self.session_button = tk.Button(
            top_frame,
            font=("Helvetica", 12),
            text=SESSION_BUTTON_DICT[self.app.session.is_active()],
            command=self._on_session_button_click,
        )
        self.session_button.pack(side=tk.LEFT, padx=2)  # Отступ между кнопкой и метками

        # Кнопка "Задним числом"
        self.retroactively_terminate_session_button = tk.Button(
            top_frame,
            font=("Helvetica", 8),
            text="Задним\nчислом",
            command=self._retroactively_terminate_session,
        )
        self.retroactively_terminate_session_button.pack(side=tk.LEFT, padx=4, ipady=0)
        self.retroactively_terminate_session_button.config(
            state=TK_BUTTON_STATES[
                self.app.session.is_active() and len(self.app.session.subsessions) > 0
            ]
        )

    def _init_middle_widgets(self):
        """Создает центральный фрейм, который состоит из фреймов таймеров"""
        timers_activities: list[int] = self.app.db.load_all_timers_activity_ids()
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=0)

        self.timer_frame_list: list[TimerFrame] = []
        duration_table = self.app.get_duration_table()
        for timer_id, activity_id in enumerate(timers_activities):
            self.timer_frame_list.append(
                TimerFrame(
                    timer_id,
                    activity_id,
                    self.app.activity_table,
                    duration_table,
                    main_frame,
                    self.on_start_timer_button,
                    self.app.session.is_active()
                )
            )

    def _init_bottom_widgets(self):
        """Создает нижние кнопки: "Стоп" и "Ручной ввод подсессии" """
        # Кнопка "Стоп"
        self.stop_timers_button = tk.Button(
            self.root,
            text="Стоп",
            command=self.on_stop_timers_button,
            font=("Helvetica", 14),
            width=30,
            height=1,
            state=TK_BUTTON_STATES[self.time_counter.is_running()],
        )
        self.stop_timers_button.pack(pady=10)

        # Кнопка "Ручной ввод подсессии"
        self.manual_input_button = tk.Button(
            self.root,
            text="Ручной ввод\nподсессии",
            command=self._manual_input_of_subsession,
            font=("Helvetica", 8),
            width=12,
            state=TK_BUTTON_STATES[self.app.session.is_active()]
        )
        self.manual_input_button.place(x=MAIN_WINDOW_X - 95, y=200)

    def _reset_timer_frames(self):
        new_duration_table = self.app.get_duration_table()
        for timer_frame in self.timer_frame_list:
            timer_frame.reset(new_duration_table)

    def _draw_session_state(self):
        if self.app.session.is_active():
            self.start_sess_datetime_label.config(text=time_to_string(self.app.session.start_time))
            self.current_session_number_label.config(text=self.app.session.id)

        self.session_label.config(text=SESSION_LABEL_DICT[self.app.session.is_active()])
        self.session_button.config(text=SESSION_BUTTON_DICT[self.app.session.is_active()]) 
        self.retroactively_terminate_session_button.config(state=TK_BUTTON_STATES[False])

        for timer in self.timer_frame_list:
            timer._gui_start_button.config(state=TK_BUTTON_STATES[self.app.session.is_active()])
        self.stop_timers_button.config(state=TK_BUTTON_STATES[self.time_counter.is_running()])
        self.manual_input_button.config(state=TK_BUTTON_STATES[self.app.session.is_active()])

    def _terminate_session(self, end_time: int) -> None:
        self.on_stop_timers_button()
        session_duration = self.app.terminate_session(end_time)
        self.start_sess_datetime_label.config(text=duration_to_string(session_duration))
        self._draw_session_state()

    def _start_session(self, start_time: int) -> None:
        self.app.start_session(start_time)
        self._reset_timer_frames()
        self._draw_session_state()

    def _on_session_button_click(self) -> None:
        click_time = int(time.time())
        if self.app.session.is_active():
            self._terminate_session(click_time)
        else:
            self._start_session(click_time)

    def _retroactively_terminate_session(self):
        RetroactivelyTerminationOfSession(
            self.root,
            self.app.session.subsessions[self.app.session.current_subsession].end_time,
            self._terminate_session
        )

    def _manual_input_of_subsession(self):
        # вот тут конечно костыль, вызванный перреставлением этого словаря в другое место
        # TODO придумать, куда деть этот словарь
        _timer_activity_names: dict[int, str] = {
            k: f"{k}. {v}" for (k, v) in self.app.activity_table.items()
        }
        ManualInputOfSubsession(self.root, _timer_activity_names, self._add_subsession_manually)

    def _add_subsession_manually(self, start_time: int, end_time: int, activity_id: int) -> None:
        self.app.add_subsession_manually(start_time, end_time, activity_id)
        new_duration_table = self.app.get_duration_table()
        for timer_frame in self.timer_frame_list:
            timer_frame.update_duration_table(new_duration_table)

    def _on_closing(self):
        self.on_stop_timers_button()
        self.app.db.save_all_timers_activity_ids(
            [timer.activity_id for timer in self.timer_frame_list]
        )
        self.root.destroy()

    def on_start_timer_button(self, id: int) -> None:
        """Запускается при нажатии на кнопку "Старт" у таймера"""
        if self.timer_frame_list[id].activity_id != self._current_activity_id:
            if self.time_counter.is_running():
                stop_time: int = self.time_counter.stop()
                self.app.terminate_subsession(stop_time)

            start_time: int = self.time_counter.start()
            self._current_activity_id = self.timer_frame_list[id].activity_id
            self.app.start_subsession(start_time, self._current_activity_id)
            self._reset_timer_frames()
        for timer in self.timer_frame_list:
            timer.setup_master(timer.id == id)

        self.stop_timers_button.config(state=TK_BUTTON_STATES[True])
        self.retroactively_terminate_session_button.config(state=TK_BUTTON_STATES[False])

    # @print_performance
    def on_stop_timers_button(self):
        """
        Запускается при нажатии на кнопку "Стоп"
        """
        if not self.time_counter.is_running():
            return

        stop_time: int = self.time_counter.stop()
        self._current_activity_id = None

        self.stop_timers_button.config(state=TK_BUTTON_STATES[False])
        self.retroactively_terminate_session_button.config(state=TK_BUTTON_STATES[True])

        self.app.terminate_subsession(stop_time)

        # Сброс таймер фреймов нужно позвать после останова подсессии,
        # т.к. они отображают состояние подсессии
        self._reset_timer_frames()

    def on_time_counter_tick(self, current_duration: int):
        for timer in self.timer_frame_list:
            timer.update_time(current_duration, self._current_activity_id)
