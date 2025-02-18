import time
import tkinter as tk
from tkinter import ttk

from common_functions import sec_to_time, time_decorator
from time_counter import TimeCounter

TK_BUTTON_STATES = {True: "normal", False: "disabled"}

# # TODO: make False in stop_timers
# should_clock_run = False

# def update_time(tk_root: tk.Tk, start_inner_timer: float, inner_timer: int) -> None:
#     """
#     Эта функция вызывает саму себя и работает до тех пор, пока хотя бы один self.running равен True
#     """
    
#     if not should_clock_run:
#         return

#     # print(
#     #     1000 * (-self.start_inner_timer + time.perf_counter()),
#     #     threading.get_ident(),
#     # )

#     self.durations_of_activities_in_current_session[self.current_activity] += 1
#     self.duration_of_all_activities += 1
    
#     for timer in TIMERS:
#         if self.running[timer]:
#             gui.time_label[timer].config(
#                 text=sec_to_time(
#                     self.durations_of_activities_in_current_session[self.activity_in_timer[timer]]
#                 )
#             )

#     inner_timer += 1

#     # threading.Timer(
#     #     int(1 + self.start_inner_timer + self.inner_timer - time.perf_counter()),
#     #     self.update_time
#     # ).start()
#     tk_root.after(
#         int(1000 * (1 + start_inner_timer + inner_timer - time.perf_counter())),
#         update_time,
#         tk_root, 
#         start_inner_timer,
#         inner_timer,
#     )
#     # Комментарий к данному куску кода:
#     # Тут мы вычисляем задержку в миллисекундах по какой-то не очень очевидной формуле, которую
#     #   я вывел математически и уже не помню, как именно это было (что-то с чем-то сократилось etc)
#     # Но факт в том: эксперимент показал, что эта формула обеспечивает посекундную синхронность
#     #   моего таймера и системных часов с точностью примерно 20мс, из-за чего не происходит
#     #   накопления ошибки
#     # Для пущей точности я НЕ выделяю эту формулу в отдельную переменную, т.к. имеет смысл максимально
#     #   сблизить момент вычисления time.perf_counter() и передачу вычисленной задержки в gui.root.after
#     # По этой же причине time.perf_counter() стоит в самом конце формулы. Небольшая, но красивая оптимизация


# def _update_time_starting(tk_root: tk.Tk):
#     """
#     Стартовая точка вхождения в поток таймера.
#     Задаёт стартовые переменные и инициирует update_time, которая потом сама себя вызывает
#     """
#     # self.updating_time = True

#     start_inner_timer: float = time.perf_counter()
#     inner_timer: int = 0

#     # TODO тут правда нужен gui? что-то странно...
#     # threading.Timer(
#     #     int(1 + self.start_inner_timer + self.inner_timer - time.perf_counter()),
#     #     self.update_time
#     # ).start()
    
#     global should_clock_run 
#     should_clock_run = True
    
#     tk_root.after(
#         int(1000 * (1 + start_inner_timer + inner_timer - time.perf_counter())),
#         update_time,
#         tk_root, 
#         start_inner_timer,
#         inner_timer,
#     )
#     # Здесь формулу оставил такой же, как и в методе update_time(): для пущей наглядности
#     # Даже не стал убирать нулевой self.timer_until_the_next_stop


class TimeTrackerTimer:
    def __init__(
            self,
            id: int,
            activity_number: int,
            gui_layer, 
            main_frame: tk.Frame,
            timer_activity_names: dict[int, str]
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
            text=sec_to_time(
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

    # def _select_activity(self, _: tk.Event[ttk.Combobox]):
    def _select_activity(self, _):  
        # Combobox считает с 0, а мы с 1
        self.activity_number = self.gui_combobox.current() + 1

        self.gui_label.config(
            text=sec_to_time(self._gui_layer.app.durations_of_activities_in_current_session[self.activity_number])
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
        Запускается при нажатии на кнопку "Старт <timer_number>"
        """
        if self.is_running:
            return

        if all(
            not timer.is_running for timer in self._gui_layer.timer_list
        ):  # старт "с нуля", т.е. все таймеры стояли
            self._starting_new_timer()
        else:  # переключение таймера, т.е. какой-то таймер работал
            self._switching_timer()

    def _starting_new_timer(self) -> None:
        for timer in self._gui_layer.timer_list:
            if timer.activity_number == self.activity_number:
                timer.is_running = True
                timer.gui_start_button.config(state=TK_BUTTON_STATES[False])
                # кстати, от этого поведения я возможно уйду: так-то прикольно было бы перекинуть
                # работающий таймер с одной позиции на другую

        self._gui_layer.app.current_activity = self.activity_number

        self.gui_combobox.config(state="disable")
        self.gui_label.config(bg="green")
        self._gui_layer.retroactively_terminate_session_button.config(state=TK_BUTTON_STATES[False])

        self._gui_layer.app.start_subs_datetime_sec = int(time.time())
        self._gui_layer.app.start_subs_by_inner_timer = 0
        # _update_time_starting()
        self._gui_layer.app.time_counter = TimeCounter(self._gui_layer)

    def _switching_timer(self) -> None:
        for timer in self._gui_layer.timer_list:
            if timer.activity_number == self.activity_number:
                timer.is_running = True
                timer.gui_start_button.config(state=TK_BUTTON_STATES[False])
                # кстати, от этого поведения я возможно уйду: так-то прикольно было бы перекинуть
                # работающий таймер с одной позиции на другую

        # приходится вызывать это дело отдельно, чтобы не было ситуации, когда any(self.running.values()) == False
        for timer in self._gui_layer.timer_list:
            if timer.activity_number != self.activity_number:
                timer.is_running = False
                timer.gui_start_button.config(state=TK_BUTTON_STATES[True])
                timer.gui_combobox.config(state="readonly")
                timer.gui_label.config(bg="SystemButtonFace")

        self.gui_combobox.config(state="disable")
        self.gui_label.config(bg="green")

        self._gui_layer.app.ending_subsession()
        self._gui_layer.app.current_activity = self.activity_number
        # вот в этом месте тоже может произойти фигня с гонкой данных
        # так-то self.current_activity используется в self.update_time
        # хм...
