# import keyboard
import time
import tkinter as tk

from common_functions import duration_to_string, print_performance, time_to_string
from gui.gui_constants import MAIN_WINDOW_X, MAIN_WINDOW_Y, SESSION_BUTTON_DICT, SESSION_LABEL_DICT, TIMERS, TK_BUTTON_STATES
from gui.manual_input_of_subsession import ManualInputOfSubsession
from gui.retroactively_termination_of_session import RetroactivelyTerminationOfSession
from gui.timer import TimeTrackerTimer
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

        app_state: dict[str, int] = self.app.db.load_app_state()

        self._timer_activity_names: dict[int, str] = {
            k: f"{k}. {v}" for (k, v) in self.app.db.get_activity_names().items()
        }

        self.init_top_frame()

        # Создаем центральный фрейм, который состоит из левого и правого фреймов
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=0)

        self.timer_list = []
        for timer_id in TIMERS:
            self.timer_list.append(
                TimeTrackerTimer(
                    timer_id,
                    app_state[f"activity_in_timer{timer_id}"],
                    self,
                    main_frame,
                    self._timer_activity_names,
                )
            )

        # Кнопка "Стоп"
        self.stop_button = tk.Button(
            self.root,
            text="Стоп",
            command=self.stop_timers,
            font=("Helvetica", 14),
            width=30,
            height=1,
            state=TK_BUTTON_STATES[self.app.is_in_session],
        )
        self.stop_button.pack(pady=10)

        # Кнопка "Ручной ввод подсессии"
        self.manual_input_button = tk.Button(
            self.root,
            text="Ручной ввод\nподсессии",
            command=self._manual_input_of_subsession,
            font=("Helvetica", 8),
            width=12,
        )
        self.manual_input_button.place(x=MAIN_WINDOW_X - 95, y=200)

        # Нужно для разработки для моментального запуска окна
        self.root.update()
        self.manual_input_button.invoke()

        # ГОРЯЧИЕ КЛАВИШИ -  имитируем нажатие нарисованных кнопок
        # keyboard.add_hotkey("Alt+F10", self.start_button[1].invoke)
        # keyboard.add_hotkey("Alt+F11", self.stop_button.invoke)
        # keyboard.add_hotkey("Alt+F12", self.start_button[2].invoke)

    def init_top_frame(self):
        # Создаем фрейм для первой строки
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)

        # Создаем метку для текста "Сессия:"
        session_text_label = tk.Label(top_frame, text="Сессия:", font=("Helvetica", 14))
        session_text_label.pack(side=tk.LEFT)

        # Создаем метку для отображения номера текущей сессии
        self.current_session_number_label = tk.Label(
            top_frame, text=self.app.session_number, font=("Helvetica", 18)
        )
        self.current_session_number_label.pack(side=tk.LEFT, padx=10)  # Отступ между метками

        # Метка для текста "Началась:"/"Длилась:"
        self.session_label = tk.Label(
            top_frame, text=SESSION_LABEL_DICT[self.app.is_in_session], font=("Helvetica", 14)
        )
        self.session_label.pack(side=tk.LEFT, padx=2)

        # Метка для времени начала сессии
        self.start_sess_datetime_label = tk.Label(
            top_frame,
            text=self.app.init_to_start_sess_datetime_label,
            font=("Helvetica", 14),
        )
        self.start_sess_datetime_label.pack(side=tk.LEFT, padx=2)

        # Кнопка "Новая сессия"/"Завершить сессию"
        self.session_button = tk.Button(
            top_frame,
            font=("Helvetica", 12),
            text=SESSION_BUTTON_DICT[self.app.is_in_session],
            command=self._on_session_button_click,
        )
        self.session_button.pack(side=tk.LEFT, padx=2)  # Отступ между кнопкой и метками

        # Кнопка "Задним числом"
        self.retroactively_terminate_session_button = tk.Button(
            top_frame,
            font=("Helvetica", 8),
            text="Задним\nчислом",
            state=TK_BUTTON_STATES[self.app.is_in_session],
            command=self._retroactively_terminate_session,
        )
        self.retroactively_terminate_session_button.pack(side=tk.LEFT, padx=4, ipady=0)
        self.retroactively_terminate_session_button.config(
            state=TK_BUTTON_STATES[bool(self.app.amount_of_subsessions) and self.app.is_in_session]
        )

    def _draw_session_state(self):
        if self.app.is_in_session:
            self.start_sess_datetime_label.config(
                text=time_to_string(self.app.current_session_start_time)
            )
            self.current_session_number_label.config(text=self.app.session_number)

        self.session_label.config(text=SESSION_LABEL_DICT[self.app.is_in_session])
        self.session_button.config(text=SESSION_BUTTON_DICT[self.app.is_in_session])

        self.retroactively_terminate_session_button.config(state=TK_BUTTON_STATES[False])
        for timer in self.timer_list:
            timer.gui_start_button.config(state=TK_BUTTON_STATES[self.app.is_in_session])
        self.stop_button.config(state=TK_BUTTON_STATES[self.app.is_in_session])

    def _terminate_session(self, end_time: int):
        self.stop_timers()
        session_duration = self.app.terminate_session(end_time)
        self.start_sess_datetime_label.config(text=duration_to_string(session_duration))
        self._draw_session_state()

    def _start_session(self):
        self.app.start_session()
        for timer in self.timer_list:
            timer.gui_label.config(text="00:00:00")
        self._draw_session_state()

    def _on_session_button_click(self):
        if self.app.is_in_session:
            self._terminate_session(int(time.time()))
        else:
            self._start_session()

    def _retroactively_terminate_session(self):
        RetroactivelyTerminationOfSession(
            self.root, self.app.end_last_subsession, self._terminate_session
        )

    def _manual_input_of_subsession(self):
        ManualInputOfSubsession(self.root, self._timer_activity_names)

    def _on_closing(self):
        self.stop_timers()
        self.app.db.save_app_state({timer.id: timer.activity_number for timer in self.timer_list})
        self.root.destroy()

    @print_performance
    def stop_timers(self):
        """
        Запускается при нажатии на кнопку "Стоп"
        """
        # TODO вот тут мы проверяем по всем таймерам, однако всегда (кроме самого начала до запуска
        #   первого таймера) тут можно использовать self.time_counter.is_running
        #   Может как-то модифицировать, чтобы можно было всегда так делать?
        #   К примеру, добавить в инициализацию TimeCounter необязательный флаг is_running.
        #       который по умолчанию будет True, но вот для первого раза будет False
        # if not any(timer.is_running for timer in self.timer_list):
        if not self.time_counter.is_running():
            return

        for timer in self.timer_list:
            timer.is_running = False

        subsession_duration: int = self.time_counter.stop()
        self.subsession.ending(subsession_duration)

        self.retroactively_terminate_session_button.config(state=TK_BUTTON_STATES[True])
        for timer in self.timer_list:
            timer.gui_combobox.config(state="readonly")
            timer.gui_start_button.config(state="normal")
            timer.gui_label.config(bg=self.DEFAULT_WIN_COLOR)

    def on_time_counter_tick(self, current_duration: int):
        for timer in self.timer_list:
            if timer.is_running:
                timer.gui_label.config(text=duration_to_string(
                    self.app.durations_of_activities_in_current_session[timer.activity_number] + current_duration
                ))
