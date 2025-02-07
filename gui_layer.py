import keyboard
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from common_functions import time_decorator, sec_to_time, time_to_sec, sec_to_datetime, datetime_to_sec
from retroactively_termination_of_session import RetroactivelyTerminationOfSession

BUTTON_PARAM_STATE_DICT = {True: "normal", False: "disabled"}
BUTTON_SESSIONS_DICT = {True: "Завершить сессию", False: "Новая сессия"}
START_TEXT_LABEL_DICT = {True: "Началась: ", False: "Длилась: "}

class GuiLayer:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("Мой трекер")
        self.root.geometry("678x250")  # Устанавливаем размер окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)  # определяем метод закрытия окна
        self.DEFAULT_WIN_COLOR = self.root.cget("background")
        
        # --- ПЕРВАЯ СТРОКА ---
        # Создаем фрейм для первой строки
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=5)

        # Создаем метку для текста "Сессия:"
        self.session_text_label = tk.Label(self.top_frame, text="Сессия:", font=("Helvetica", 14))
        self.session_text_label.pack(side=tk.LEFT)

        # Создаем метку для отображения номера текущей сессии
        self.current_session_value_label = tk.Label(
            self.top_frame,
            text=app.session_number,
            font=("Helvetica", 18)
        )
        self.current_session_value_label.pack(side=tk.LEFT, padx=10)  # Отступ между метками

        # Метка для текста "Началась:"/"Длилась:"
        self.start_text_label = tk.Label(
            self.top_frame,
            text=START_TEXT_LABEL_DICT[app.is_in_session],
            font=("Helvetica", 14)
        )
        self.start_text_label.pack(side=tk.LEFT, padx=2)

        # Метка для времени начала сессии
        self.start_sess_datetime_label = tk.Label(
            self.top_frame,
            text=app.start_current_session if app.is_in_session else app.duration_current_session,
            font=("Helvetica", 14)
        )
        self.start_sess_datetime_label.pack(side=tk.LEFT, padx=2)

        # Кнопка "Новая сессия"/"Завершить сессию"
        self.startterminate_session_button = tk.Button(
            self.top_frame,
            font=("Helvetica", 12),
            text=BUTTON_SESSIONS_DICT[app.is_in_session],
            command=app.startterminate_session
        )
        self.startterminate_session_button.pack(side=tk.LEFT, padx=2)  # Отступ между кнопкой и метками
        
        # Кнопка "Задним числом"
        self.retroactively_terminate_session_button = tk.Button(
            self.top_frame,
            font=("Helvetica", 8),
            text="Задним\nчислом",
            state=BUTTON_PARAM_STATE_DICT[app.is_in_session],
            command=self._retroactively_terminate_session
        )
        self.retroactively_terminate_session_button.pack(side=tk.LEFT, padx=4, ipady=0)
        self.retroactively_terminate_session_button.config(
            state=BUTTON_PARAM_STATE_DICT[bool(app.amount_of_subsessions) and app.is_in_session]
        )
        
        # --- ДВЕ ПОЛОВИНЫ ---
        # Создаем фрейм для разделения на две половины
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(pady=0)

        # Левая половина
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, padx=50)

        # Часы 1
        self.time_1_label = tk.Label(
            self.left_frame,
            text=sec_to_time(app.durations_of_activities_in_current_session[app.activity_in_timer1]),
            font=("Helvetica", 36)
        )
        self.time_1_label.pack()

        # Комбобокс 1
        self.combobox_1_value = tk.StringVar()  # нужен для работа с выбранным значением комбобокса
        self.combobox_1 = ttk.Combobox(
            self.left_frame,
            textvariable=self.combobox_1_value,
            values=list(app.activities_dict_to_show.values()),
            state='readonly'
        )
        self.combobox_1.pack(pady=5)
        self.combobox_1_value.set(app.activities_dict_to_show[app.activity_in_timer1])
        self.combobox_1.bind("<<ComboboxSelected>>", app.on_select_combo_1)

        # Кнопка "Старт 1"
        self.start1_button = tk.Button(
            self.left_frame,
            text="Старт 1",
            command=app.start_timer_1,
            font=("Helvetica", 14),
            width=10,
            height=1, 
            state=BUTTON_PARAM_STATE_DICT[app.is_in_session]
        )
        self.start1_button.pack(pady=5)

        # Правая половина
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, padx=50)

        # Часы 2
        self.time_2_label = tk.Label(
            self.right_frame,
            text=sec_to_time(app.durations_of_activities_in_current_session[app.activity_in_timer2]),
            font=("Helvetica", 36)
        )
        self.time_2_label.pack()

        # Комбобокс 2
        self.combobox_2_value = tk.StringVar()  # нужен для работа с выбранным значением комбобокса
        self.combobox_2 = ttk.Combobox(
            self.right_frame,
            textvariable=self.combobox_2_value,
            values=list(app.activities_dict_to_show.values()),
            state='readonly'
        )
        self.combobox_2.pack(pady=5)
        self.combobox_2_value.set(app.activities_dict_to_show[app.activity_in_timer2])
        self.combobox_2.bind("<<ComboboxSelected>>", app.on_select_combo_2)

        # Кнопка "Старт 2"
        self.start2_button = tk.Button(
            self.right_frame,
            text="Старт 2",
            command=app.start_timer_2,
            font=("Helvetica", 14),
            width=10,
            height=1, 
            state=BUTTON_PARAM_STATE_DICT[app.is_in_session]
        )
        self.start2_button.pack(pady=5)

        # Кнопка "Стоп" внизу
        self.stop_button = tk.Button(
            root,
            text="Стоп",
            command=app.stop_timers,
            font=("Helvetica", 14),
            width=30,
            height=1, 
            state=BUTTON_PARAM_STATE_DICT[app.is_in_session]
        )
        self.stop_button.pack(pady=10)
        
        # ГОРЯЧИЕ КЛАВИШИ -  имитируем нажатие нарисованных кнопок
        keyboard.add_hotkey('Alt+F10', self.start1_button.invoke)
        keyboard.add_hotkey('Alt+F11', self.stop_button.invoke)
        keyboard.add_hotkey('Alt+F12', self.start2_button.invoke)        
        
    def _retroactively_terminate_session(self):
        RetroactivelyTerminationOfSession(self.root, self.app)

    def _on_closing(self):
        self.app.stop_timers()
        self.app.db.save_app_state(self.app.activity_in_timer1, self.app.activity_in_timer2)
        self.root.destroy()
