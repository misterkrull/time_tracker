import keyboard
import time
import tkinter as tk
from typing import Any

from application_logic import ApplicationLogic
from common_functions import duration_to_string, forming_activities_for_combobox, print_performance, time_to_string
from gui.gui_constants import (
    SESSION_BUTTON_DICT, SESSION_LABEL_DICT,
    TK_BUTTON_STATES,
)
from gui.manual_input_of_subsession_simple import ManualInputOfSubsessionSimple
from gui.retroactively_termination_of_session import RetroactivelyTerminationOfSession
from gui.timer_frame import TimerFrame
from time_counter import TimeCounter


class GuiLayer:
    def __init__(self, root: tk.Tk, app: ApplicationLogic, settings: dict[str, Any]):
        self.root = root
        self.app = app

        self._settings = settings
        self._main_window_x: int = settings["main_window_x"]
        self._main_window_y: int = settings["main_window_y"]
        _main_window_position_x: int = settings["main_window_position_x"]
        _main_window_position_y: int = settings["main_window_position_y"]

        self.root.title("Мой трекер")
        self.root.geometry(
            f"{self._main_window_x}x{self._main_window_y}+{_main_window_position_x}+{_main_window_position_y}"
        )
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

        if settings["enable_global_hotkeys"]:
            keyboard.add_hotkey("Alt + F9", self.timer_frame_list[0].gui_start_button.invoke)
            keyboard.add_hotkey("Alt + F10", self.timer_frame_list[1].gui_start_button.invoke)
            keyboard.add_hotkey("Alt + F11", self.timer_frame_list[2].gui_start_button.invoke)
            keyboard.add_hotkey("Alt + F12", self.stop_timers_button.invoke)
            keyboard.add_hotkey("Alt Gr + F9", self.timer_frame_list[0].gui_start_button.invoke)
            keyboard.add_hotkey("Alt Gr + F10", self.timer_frame_list[1].gui_start_button.invoke)
            keyboard.add_hotkey("Alt Gr + F11", self.timer_frame_list[2].gui_start_button.invoke)
            keyboard.add_hotkey("Alt Gr + F12", self.stop_timers_button.invoke)

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
                    self.app.activities_table,
                    duration_table,
                    main_frame,
                    self.on_start_timer_button,
                    self.app.session.is_active(),
                    self._settings
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
        self.manual_input_button.place(x=self._main_window_x - 95, y=200)

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
            timer.gui_start_button.config(state=TK_BUTTON_STATES[self.app.session.is_active()])
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
        # в случае активной подсессии нужно передать окну ручного ввода номер активности (для значения
        #   по умолчанию у комбобокса), а также время её начала
        if (
            self.app.session.current_subsession is not None
            and self.app.session.subsessions[self.app.session.current_subsession].is_active()
        ):
            current_activity = self.app.session.subsessions[self.app.session.current_subsession].activity_id
            start_current_subsession = self.app.session.subsessions[self.app.session.current_subsession].start_time
        else:
            current_activity = None
            start_current_subsession = None

        # для вычисления рекомендуемого максимального времени ручной сессии требуется найти время окончания предыдущей
        if self.app.session.current_subsession is not None and self.app.session.current_subsession > 0:
            end_previous_subsession = max(  # зачем тут max и for - см. длинный коммент ниже
                [
                    self.app.session.subsessions[subsession_number].end_time
                    for subsession_number in range(0, self.app.session.current_subsession)
                ]
            )
        else:
            end_previous_subsession = None

        # Здесь надо понимать, что end_previous_subsession - это подсессия, предыдущая перед текущей подсессией
        #   по номеру подсессии в списке self.app.session.subsessions
        # Однако оно НЕ ОЗНАЧАЕТ, что это ПОСЛЕДНЯЯ ПОДСЕССИЯ В БД !!!
        # А всё потому, что между start_current_subsession и настоящим моментом могут быть в ручном режиме
        #   введены ещё подсесии! И мы тогда их не учтём.
        # Впрочем, они нам не то, чтобы не нужны, но даже и мешались бы, т.к. замысел всей этой фигни таков, что
        #   мы позже нужного начали текущую подсессию, и нам нужно замерять интервал именно(!) между началом текущей
        #   подсессии и концом той, которая была до неё! Подсессии, введённые в ручном режиме во время работы текущей
        #   подсессии, во-первых нам (как было сказано) не нужны, а во-вторых - по замыслу им так неоткуда взяться,
        #   т.к. мы, поздно спохватившись, стартовали эту текущую подсессию и СРАЗУ ЖЕ стали вбивать пропущенное время.
        # 
        # Тут впрочем имеется другая проблема: в промежутке между окончанием предыдущей автоматической подсессией
        #   и началом текущей могут быть в ручном режиме введены какие-то совершенно левые подсессии, и вот тогда 
        #   мы будем учитывать окончание последней из них, что может дать совершенно произвольные результаты!
        # Именно по этой причине приходится вместо окончанием буквально предыдущей сессии искать максимум среди 
        #   окончаний всех подсессий, которые были введены ДО текущей.
        # 
        # Хотя конечно в итоге от длительности этого безподсессионного промежутка ничего не зависит, т.к. это величина
        #   рекомендованная. Так что и на том, что уже есть, спасибо.

        ManualInputOfSubsessionSimple(
            self.root,
            forming_activities_for_combobox(self.app.activities_table, self._settings), 
            self._settings["combobox_height"],
            self._add_subsession_manually,
            current_activity,
            start_current_subsession,
            end_previous_subsession
        )

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
        assert self._current_activity_id
        for timer in self.timer_frame_list:
            timer.update_time(current_duration, self._current_activity_id)
