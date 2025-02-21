# import keyboard
import time
import tkinter as tk

# TODO: import after gui separation
# from time_tracker import ApplicationLogic
from common_functions import duration_to_string, time_decorator, TIMERS
from retroactively_termination_of_session import RetroactivelyTerminationOfSession
from timer import TimeTrackerTimer
from time_counter import TimeCounter


BUTTON_SESSIONS_DICT = {True: "Завершить сессию", False: "Новая сессия"}
START_TEXT_LABEL_DICT = {True: "Началась: ", False: "Длилась: "}
BUTTON_PARAM_STATE_DICT = {True: "normal", False: "disabled"}


class GuiLayer:
    def __init__(self, root, app):
        self.root = root
        self.app = app

        self.root.title("Мой трекер")
        self.root.geometry("678x250")  # Устанавливаем размер окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)  # определяем метод закрытия окна
        self.DEFAULT_WIN_COLOR = self.root.cget("background")

        self.time_counter = TimeCounter(
            tk_root=self.root, on_tick_function=self.on_time_counter_tick
        )

        app_state: dict[str, int] = self.app.db.load_app_state()

        timer_activity_names: dict[int, str] = {
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
                    timer_activity_names,
                )
            )

        # Кнопка "Стоп" внизу
        self.stop_button = tk.Button(
            self.root,
            text="Стоп",
            command=self.stop_timers,
            font=("Helvetica", 14),
            width=30,
            height=1,
            state=BUTTON_PARAM_STATE_DICT[self.app.is_in_session],
        )
        self.stop_button.pack(pady=10)

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
        self.current_session_value_label = tk.Label(
            top_frame, text=self.app.session_number, font=("Helvetica", 18)
        )
        self.current_session_value_label.pack(side=tk.LEFT, padx=10)  # Отступ между метками

        # Метка для текста "Началась:"/"Длилась:"
        self.start_text_label = tk.Label(
            top_frame, text=START_TEXT_LABEL_DICT[self.app.is_in_session], font=("Helvetica", 14)
        )
        self.start_text_label.pack(side=tk.LEFT, padx=2)

        # Метка для времени начала сессии
        self.start_sess_datetime_label = tk.Label(
            top_frame,
            text=self.app.init_to_start_sess_datetime_label,
            font=("Helvetica", 14),
        )
        self.start_sess_datetime_label.pack(side=tk.LEFT, padx=2)

        # Кнопка "Новая сессия"/"Завершить сессию"
        self.startterminate_session_button = tk.Button(
            top_frame,
            font=("Helvetica", 12),
            text=BUTTON_SESSIONS_DICT[self.app.is_in_session],
            command=self.app.startterminate_session,
        )
        self.startterminate_session_button.pack(
            side=tk.LEFT, padx=2
        )  # Отступ между кнопкой и метками

        # Кнопка "Задним числом"
        self.retroactively_terminate_session_button = tk.Button(
            top_frame,
            font=("Helvetica", 8),
            text="Задним\nчислом",
            state=BUTTON_PARAM_STATE_DICT[self.app.is_in_session],
            command=self._retroactively_terminate_session,
        )
        self.retroactively_terminate_session_button.pack(side=tk.LEFT, padx=4, ipady=0)
        self.retroactively_terminate_session_button.config(
            state=BUTTON_PARAM_STATE_DICT[
                bool(self.app.amount_of_subsessions) and self.app.is_in_session
            ]
        )

    def _retroactively_terminate_session(self):
        RetroactivelyTerminationOfSession(
            self.root, self.app.end_last_subsession, self.app.startterminate_session
        )

    def _on_closing(self):
        self.stop_timers()
        self.app.db.save_app_state({timer.id: timer.activity_number for timer in self.timer_list})
        self.root.destroy()

    @time_decorator
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
        if not self.time_counter.is_running:
            return

        for timer in self.timer_list:
            timer.is_running = False

        self.time_counter.stop()
        self.subsession.ending(time.time())

        self.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[True])
        for timer in self.timer_list:
            timer.gui_combobox.config(state="readonly")
            timer.gui_start_button.config(state="normal")
            timer.gui_label.config(bg=self.DEFAULT_WIN_COLOR)

    def on_time_counter_tick(self):
        self.app.durations_of_activities_in_current_session[self.app.current_activity] += 1
        self.app.duration_of_all_activities += 1

        for timer in self.timer_list:
            if timer.is_running:
                timer.gui_label.config(
                    text=duration_to_string(
                        self.app.durations_of_activities_in_current_session[timer.activity_number]
                    )
                )
