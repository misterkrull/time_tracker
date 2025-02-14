import keyboard
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from common_functions import sec_to_time, TIMERS
from retroactively_termination_of_session import RetroactivelyTerminationOfSession


BUTTON_PARAM_STATE_DICT = {
    True: "normal", 
    False: "disabled"
}
BUTTON_SESSIONS_DICT = {
    True: "Завершить сессию", 
    False: "Новая сессия"
}
START_TEXT_LABEL_DICT = {
    True: "Началась: ",
    False: "Длилась: "
}


class GuiLayer:
    def __init__(self, root, app):
        self.root = root
        self.app = app

        self.root.title("Мой трекер")
        self.root.geometry("678x250")  # Устанавливаем размер окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)  # определяем метод закрытия окна
        self.DEFAULT_WIN_COLOR = self.root.cget("background")
        
        self.init_top_frame()

        # Создаем центральный фрейм, который состоит из левого и правого фреймов
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=0)

        # инициализируем словари виджетов
        self.time_label = {}
        self.combobox_value = {}
        self.combobox = {}
        self.start_button = {}                        

        for timer in TIMERS:
            self.init_timer_frame(main_frame, timer)

        # Кнопка "Стоп" внизу
        self.stop_button = tk.Button(
            self.root,
            text="Стоп",
            command=self.app.stop_timers,
            font=("Helvetica", 14),
            width=30,
            height=1, 
            state=BUTTON_PARAM_STATE_DICT[self.app.is_in_session]
        )
        self.stop_button.pack(pady=10)
        
        # ГОРЯЧИЕ КЛАВИШИ -  имитируем нажатие нарисованных кнопок
        keyboard.add_hotkey('Alt+F10', self.start_button[1].invoke)
        keyboard.add_hotkey('Alt+F11', self.stop_button.invoke)
        keyboard.add_hotkey('Alt+F12', self.start_button[2].invoke)
    
    def init_top_frame(self):
        # Создаем фрейм для первой строки
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)

        # Создаем метку для текста "Сессия:"
        session_text_label = tk.Label(
            top_frame,
            text="Сессия:",
            font=("Helvetica", 14)
        )
        session_text_label.pack(side=tk.LEFT)

        # Создаем метку для отображения номера текущей сессии
        self.current_session_value_label = tk.Label(
            top_frame,
            text=self.app.session_number,
            font=("Helvetica", 18)
        )
        self.current_session_value_label.pack(side=tk.LEFT, padx=10)  # Отступ между метками

        # Метка для текста "Началась:"/"Длилась:"
        self.start_text_label = tk.Label(
            top_frame,
            text=START_TEXT_LABEL_DICT[self.app.is_in_session],
            font=("Helvetica", 14)
        )
        self.start_text_label.pack(side=tk.LEFT, padx=2)

        # Метка для времени начала сессии
        self.start_sess_datetime_label = tk.Label(
            top_frame,
            text=self.app.start_current_session if self.app.is_in_session else self.app.duration_current_session,
            font=("Helvetica", 14)
        )
        self.start_sess_datetime_label.pack(side=tk.LEFT, padx=2)

        # Кнопка "Новая сессия"/"Завершить сессию"
        self.startterminate_session_button = tk.Button(
            top_frame,
            font=("Helvetica", 12),
            text=BUTTON_SESSIONS_DICT[self.app.is_in_session],
            command=self.app.startterminate_session
        )
        self.startterminate_session_button.pack(side=tk.LEFT, padx=2)  # Отступ между кнопкой и метками
        
        # Кнопка "Задним числом"
        self.retroactively_terminate_session_button = tk.Button(
            top_frame,
            font=("Helvetica", 8),
            text="Задним\nчислом",
            state=BUTTON_PARAM_STATE_DICT[self.app.is_in_session],
            command=self._retroactively_terminate_session
        )
        self.retroactively_terminate_session_button.pack(side=tk.LEFT, padx=4, ipady=0)
        self.retroactively_terminate_session_button.config(
            state=BUTTON_PARAM_STATE_DICT[bool(self.app.amount_of_subsessions) and self.app.is_in_session]
        )

    def init_timer_frame(self, main_frame: tk.Frame, timer_number: int):
        timer_frame = tk.Frame(main_frame)
        timer_frame.pack(
            side=tk.LEFT,
            padx=10
        )

        # Таймер
        self.time_label[timer_number] = tk.Label(
            timer_frame,
            text=sec_to_time(self.app.durations_of_activities_in_current_session[self.app.activity_in_timer[timer_number]]),
            font=("Helvetica", 36)
        )
        self.time_label[timer_number].pack()

        # Комбобокс
        self.combobox_value[timer_number] = tk.StringVar()  # нужен для работа с выбранным значением комбобокса
        self.combobox[timer_number] = ttk.Combobox(
            timer_frame,
            textvariable=self.combobox_value[timer_number],
            values=list(self.app.activities_dict_to_show.values()),
            state='readonly'
        )
        self.combobox[timer_number].pack(pady=5)
        self.combobox_value[timer_number].set(self.app.activities_dict_to_show[self.app.activity_in_timer[timer_number]])
        self.combobox[timer_number].bind("<<ComboboxSelected>>", lambda event: self.app.on_select_combo(timer_number))

        # Кнопка "Старт <timer_number>"
        self.start_button[timer_number] = tk.Button(
            timer_frame,
            text=f"Старт {timer_number}",
            command=lambda: self.app.start_timer(timer_number),
            font=("Helvetica", 14),
            width=10,
            height=1, 
            state=BUTTON_PARAM_STATE_DICT[self.app.is_in_session]
        )
        self.start_button[timer_number].pack(pady=5)

    def _retroactively_terminate_session(self):
        RetroactivelyTerminationOfSession(self.root, self.app)

    def _on_closing(self):
        self.app.stop_timers()
        self.app.db.save_app_state(self.app.activity_in_timer)
        self.root.destroy()
