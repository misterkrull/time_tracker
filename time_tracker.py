import keyboard
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from common_functions import time_decorator, sec_to_time, time_to_sec, sec_to_datetime, datetime_to_sec, TIMERS
from db_manager import DB
from gui_layer import GuiLayer, BUTTON_PARAM_STATE_DICT, BUTTON_SESSIONS_DICT, START_TEXT_LABEL_DICT


class ApplicationLogic:
    def __init__(self):
        self.db = DB()

        self.activities_dict: dict[int, str] = self.db.get_activities()
        self.activities_dict_to_show: dict[int, str] = {k:f"{k}. {v}" for (k, v) in self.activities_dict.items()}
        self.amount_of_activities: int = len(self.activities_dict)
        
        last_session: tuple | None = self.db.get_last_session()
        if last_session == None:  # случай, если у нас ещё не было ни одной сессии (т.е. новая БД)
            # TODO может быть убрать отсюда те переменные, которые нам будут не нужны?
            # однако если убрать, то эти переменные будут объявлены в другом месте
            #   их там в другом месте надо будет аннотировать? вот вопрос...
            self.is_in_session: bool = False                    # ЭТО НУЖНО
            self.session_number: int = 0                        # ЭТО НУЖНО
            self.start_current_session: str = "00:00:00"        # это не нужно
            self.start_current_session_sec: int = 0.0         # это не нужно
            self.duration_current_session: str = "--:--:--"     # ЭТО НУЖНО
            self.duration_current_session_sec: int = 0          # это не нужно
            self.durations_of_activities_in_current_session: dict[int, int] = {
                i + 1: 0 for i in range(self.amount_of_activities)
            }  # у нас
        else:
            self.is_in_session: bool = ( last_session[2] == "---" )
            self.session_number: int = last_session[0]
            self.start_current_session: str = last_session[1]
            self.start_current_session_sec: int = datetime_to_sec(self.start_current_session)
            self.duration_current_session: str = last_session[3]
            self.duration_current_session_sec: int = time_to_sec(self.duration_current_session)
                # нам в зависимости от is_in_session нужно будет либо start_current_session,
                #                                                либо duration_current_session
            self.durations_of_activities_in_current_session: dict[int, int] = {
                i + 1: v for i, v in enumerate(
                    map(time_to_sec, last_session[-self.amount_of_activities:])
                )
            }
        self.duration_of_all_activities: int = sum(self.durations_of_activities_in_current_session.values())

        self.amount_of_subsessions: int = self.db.get_amount_of_subsessions(self.session_number)
        # print("Количество подсессий:", self.amount_of_subsessions)
        if self.amount_of_subsessions > 0:
            self.end_subs_datetime_sec: int = datetime_to_sec(self.db.get_datetime_of_last_subsession())
        # это нужно для работы кнопки "Завершить сессию задним числом"
        # проверка self.amount_of_subsessions > 0 по сути ничего не даёт:
        #   если self.amount_of_subsessions == 0, то у нас кнопка "Задним числом" засерена
        # однако же если у нас ещё ВООБЩЕ не подсессий, то get_datetime_of_last_subsession будет пуст
        # да, тут логичнее было бы проверить количество подсессий во всей таблице subsessions!
        # но у нас такого параметра нет, поэтому проверяем как можем

        app_state: dict[str, int] = self.db.load_app_state()
        self.activity_in_timer: dict[int, int] = {}
        for timer in TIMERS:
            self.activity_in_timer[timer] = app_state[f'activity_in_timer{timer}']

        self.running: dict[int, bool] = {timer: False for timer in TIMERS}

    def on_select_combo(self, timer_number: int):
        self.on_select_combo_new(timer_number)

    def on_select_combo_old(self, timer_number: int):
        self.activity_in_timer[timer_number] = gui.combobox[timer_number].current() + 1  # слева отсчёт с 1, справа -- с 0; 
        gui.time_label[timer_number].config(
            text=sec_to_time(self.durations_of_activities_in_current_session[self.activity_in_timer[timer_number]])
        )
        if any(self.running.values()):
            if self.activity_in_timer[1] == self.activity_in_timer[2]:
                self.running[timer_number] = True
                gui.start_button[timer_number].config(state=BUTTON_PARAM_STATE_DICT[False])
            else:
                self.running[timer_number] = False
                gui.start_button[timer_number].config(state=BUTTON_PARAM_STATE_DICT[True])

    def on_select_combo_new(self, timer_number: int):
        self.activity_in_timer[timer_number] = gui.combobox[timer_number].current() + 1  # слева отсчёт с 1, справа с 0
        gui.time_label[timer_number].config(
            text=sec_to_time(self.durations_of_activities_in_current_session[self.activity_in_timer[timer_number]])
        )

        for timer in set(TIMERS) - {timer_number}:
            if self.running[timer]:
                if self.activity_in_timer[timer] == self.activity_in_timer[timer_number]:
                    self.running[timer_number] = True
                    gui.start_button[timer_number].config(state=BUTTON_PARAM_STATE_DICT[False])
                else:                    
                    self.running[timer_number] = False
                    gui.start_button[timer_number].config(state=BUTTON_PARAM_STATE_DICT[True])
                break

    def start_session(self):
        self.is_in_session = True
        self.session_number += 1
        for activity in self.durations_of_activities_in_current_session.keys():
            self.durations_of_activities_in_current_session[activity] = 0
        self.duration_of_all_activities = 0
        self.amount_of_subsessions = 0
        self.start_current_session_sec: int = int(time.time())
        self.start_current_session = sec_to_datetime(self.start_current_session_sec)

        self.db.create_new_session(
            self.session_number,
            self.start_current_session,
            self.amount_of_activities
        )
        
        gui.start_sess_datetime_label.config(text=self.start_current_session)
        gui.current_session_value_label.config(text=self.session_number)
        for timer in TIMERS:
            gui.time_label[timer].config(text="00:00:00")

    def terminate_session(self, retroactively=False):
        self.is_in_session = False
        self.stop_timers()

        if not retroactively:
            self.end_current_session_sec = int(time.time())
        self.end_current_session = sec_to_datetime(self.end_current_session_sec)
        self.duration_current_session_sec = self.end_current_session_sec - self.start_current_session_sec
        self.duration_current_session = sec_to_time(self.duration_current_session_sec)
        self.db.complete_new_session(
            self.session_number,
            self.end_current_session,
            self.duration_current_session
        )
            
        gui.start_sess_datetime_label.config(text=self.duration_current_session)

    def startterminate_session(self, retroactively=False):
        if self.is_in_session:
            self.terminate_session(retroactively)
        else:
            self.start_session()

        # вот это всё безобразие может быть надо по обеим функциям распихать?
        # тогда эти строчки повторяется по два раза, однако возможно будет нагляднее
        # однако если оставлять так, как есть, то может быть смену флага is_in_session нужно будет
        #   из обеих функций вытащить сюда, чтобы было наглядно видно, что флаг этот меняется, вообще-то
        gui.start_text_label.config(text=START_TEXT_LABEL_DICT[self.is_in_session])
        gui.startterminate_session_button.config(text=BUTTON_SESSIONS_DICT[self.is_in_session])

        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[False])
        for timer in TIMERS:
            gui.start_button[timer].config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        gui.stop_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
            
    def update_time(self):
        """
Эта функция вызывает саму себя и работает до тех пор, пока хотя бы один self.running равен True
        """
       
        if not any(self.running.values()):
            # self.updating_time = False
            return
        print(1000*(- self.start_inner_timer + time.perf_counter()), threading.get_ident())

        self.durations_of_activities_in_current_session[self.current_activity] += 1
        self.duration_of_all_activities += 1
        for timer in TIMERS:
            if self.running[timer]:
                gui.time_label[timer].config(
                    text=sec_to_time(self.durations_of_activities_in_current_session[self.activity_in_timer[timer]])
                )

        self.inner_timer += 1

        # threading.Timer(
        #     int(1 + self.start_inner_timer + self.inner_timer - time.perf_counter()),
        #     self.update_time
        # ).start()
        gui.root.after(
            int(1000*(1 + self.start_inner_timer + self.inner_timer - time.perf_counter())),
            self.update_time
        )
        # Комментарий к данному куску кода:
        # Тут мы вычисляем задержку в миллисекундах по какой-то не очень очевидной формуле, которую
        #   я вывел математически и уже не помню, как именно это было (что-то с чем-то сократилось etc)
        # Но факт в том: эксперимент показал, что эта формула обеспечивает посекундную синхронность
        #   моего таймера и системных часов с точностью примерно 20мс, из-за чего не происходит
        #   накопления ошибки
        # Для пущей точности я НЕ выделяю эту формулу в отдельную переменную, т.к. имеет смысл максимально
        #   сблизить момент вычисления time.perf_counter() и передачу вычисленной задержки в gui.root.after
        # По этой же причине time.perf_counter() стоит в самом конце формулы. Небольшая, но красивая оптимизация

    def update_time_starting(self):
        """
Стартовая точка вхождения в поток таймера.
Задаёт стартовые переменные и инициирует update_time, которая потом сама себя вызывает
        """
        # self.updating_time = True

        self.start_inner_timer: float = time.perf_counter()
        self.inner_timer: int = 0

        self.start_subs_datetime_sec: int = int(time.time())
        self.start_subs_by_inner_timer: int = 0

        print("Поток:", threading.get_ident())
        # TODO тут правда нужен gui? что-то странно...
        # threading.Timer(
        #     int(1 + self.start_inner_timer + self.inner_timer - time.perf_counter()),
        #     self.update_time
        # ).start()
        gui.root.after(
            int(1000*(1 + self.start_inner_timer + self.inner_timer - time.perf_counter())),
            self.update_time
        )
        # Здесь формулу оставил такой же, как и в методе update_time(): для пущей наглядности
        # Даже не стал убирать нулевой self.timer_until_the_next_stop

    @time_decorator
    def start_timer(self, timer_number: int):
        """
Запускается при нажатии на кнопку "Старт <timer_number>"
        """
        self.start_timer_new(timer_number)

    def start_timer_old(self, timer_number: int):
        print(threading.get_ident())
        if self.running[timer_number]:
            return
        self.running[timer_number] = True
        if not self.running[3 - timer_number]:          # если другой таймер стоял (т.е. оба таймера стояли; старт с "нуля")
            self.current_activity: int = self.activity_in_timer[timer_number]
            if self.activity_in_timer[3 - timer_number] == self.activity_in_timer[timer_number]:
                self.running[3 - timer_number] = True
                gui.start_button[3 - timer_number].config(state=BUTTON_PARAM_STATE_DICT[False])
            self.update_time_starting()
            # threading.Thread(target=self.update_time_starting, daemon=True).start()
        else:                           # если другой таймер шёл (т.е. происходит переключение таймера)
            self.running[3 - timer_number] = False
            self.ending_subsession()
            self.current_activity: int = self.activity_in_timer[timer_number]
                
        gui.combobox[timer_number].config(state='disabled')
        gui.combobox[3 - timer_number].config(state='readonly')
        gui.time_label[timer_number].config(bg='green')
        gui.time_label[3 - timer_number].config(bg=gui.DEFAULT_WIN_COLOR)
        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[False])

    @time_decorator
    def start_timer_new(self, timer_number: int) -> None:
        if self.running[timer_number]:
            return
        if not any(self.running.values()):  # старт "с нуля", т.е. все таймеры стояли
            self.starting_new_timer(timer_number)
        else:                               # переключение таймера, т.е. какой-то таймер работал
            self.switching_timer(timer_number)
            
    def starting_new_timer(self, timer_number: int) -> None:
        for timer in TIMERS:
            if self.activity_in_timer[timer] == self.activity_in_timer[timer_number]:
                self.running[timer] = True
                if timer != timer_number:
                    gui.start_button[timer].config(state=BUTTON_PARAM_STATE_DICT[False])
                    # кстати, от этого поведения я возможно уйду: так-то прикольно было бы перекинуть
                    # работающий таймер с одной позиции на другую

        self.current_activity: int = self.activity_in_timer[timer_number]

        gui.combobox[timer_number].config(state='disable')
        gui.time_label[timer_number].config(bg='green')
        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[False])

        self.update_time_starting()

    def switching_timer(self, timer_number: int) -> None:
        for timer in TIMERS:
            if self.activity_in_timer[timer] == self.activity_in_timer[timer_number]:
                self.running[timer] = True
                if timer != timer_number:
                    gui.start_button[timer].config(state=BUTTON_PARAM_STATE_DICT[False])
                    # кстати, от этого поведения я возможно уйду: так-то прикольно было бы перекинуть
                    # работающий таймер с одной позиции на другую
        # приходится вызывать это дело отдельно, чтобы не было ситуации, когда any(self.running.values()) == False
        for timer in TIMERS:
            if self.activity_in_timer[timer] != self.activity_in_timer[timer_number]:
                self.running[timer] = False
                gui.start_button[timer].config(state=BUTTON_PARAM_STATE_DICT[True])
                gui.combobox[timer].config(state='readonly')
                gui.time_label[timer].config(bg=gui.DEFAULT_WIN_COLOR)

        gui.combobox[timer_number].config(state='disable')
        gui.time_label[timer_number].config(bg='green')

        self.ending_subsession()
        self.current_activity: int = self.activity_in_timer[timer_number]
            # вот в этом месте тоже может произойти фигня с гонкой данных
            # так-то self.current_activity используется в self.update_time
            # хм...

    @time_decorator
    def stop_timers(self):
        """
Запускается при нажатии на кнопку "Стоп"
        """
        if not any(self.running.values()):
            return
        self.running = {timer: False for timer in TIMERS}
        self.ending_subsession()

        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[True])
        for timer in TIMERS:
            gui.combobox[timer].config(state='readonly')
            gui.start_button[timer].config(state='normal')
            gui.time_label[timer].config(bg=gui.DEFAULT_WIN_COLOR)

    def ending_subsession(self):
        self.subs_duration_sec: int = self.inner_timer - self.start_subs_by_inner_timer
        self.end_subs_datetime_sec: int = self.start_subs_datetime_sec + self.subs_duration_sec

        # обновляем время старта по inner_timer для следующей подсессии (если она будет)
        self.start_subs_by_inner_timer = self.inner_timer
        
        # обновляем глобальное время старта для следующей подсессии (если она будет)
        # делаем это сейчас, т.к. впереди у нас дооолгий запрос к БД
        # однако пишем во временную переменную, т.к. self.start_subs_datetime_sec ещё потребуется для передачи в БД
        # после передачи в БД мы и обновим self.start_subs_datetime_sec
        start_next_subs_datetime_sec: int = int(time.time())
        # вообще говоря это костыль, а по уму нужно делать асинхронку или что-то в этом духе
        # TODO убрать этот костыль и сделать по уму

        self.amount_of_subsessions += 1
        
        # да, здесь нужна двойная функция: чтобы сразу два запроса к БД одним махом пульнуть
        # экономия времени существенная! замерял!
        self.db.add_new_subsession_and_update_current_session(
            self.session_number,
            self.current_activity,
            sec_to_datetime(self.start_subs_datetime_sec),
            sec_to_datetime(self.end_subs_datetime_sec),
            sec_to_time(self.subs_duration_sec),
            self.amount_of_subsessions,
            sec_to_time(self.duration_of_all_activities),
            sec_to_time(self.durations_of_activities_in_current_session[self.current_activity])
        )
        
        self.start_subs_datetime_sec = start_next_subs_datetime_sec


if __name__ == "__main__":
    app = ApplicationLogic()
    root = tk.Tk()
    gui = GuiLayer(root, app)
    root.mainloop()