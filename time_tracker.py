import keyboard
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from common_functions import time_decorator, sec_to_time, time_to_sec, sec_to_datetime, datetime_to_sec
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
            self.start_current_session_sec: float = 0.0         # это не нужно
            self.duration_current_session: str = "--:--:--"     # ЭТО НУЖНО
            self.duration_current_session_sec: int = 0          # это не нужно
            # TODO разобрать с int и float у start_current_session_sec и duration_current_session_sec
            #   т.е. почему в одном случае одно, а в другом -- другое
            self.durations_of_activities_in_current_session: dict[int, int] = {
                i + 1: 0 for i in range(self.amount_of_activities)
            }  # у нас
        else:
            self.is_in_session: bool = ( last_session[2] == "---" )
            self.session_number: int = last_session[0]
            self.start_current_session: str = last_session[1]
            self.start_current_session_sec: float = float(datetime_to_sec(self.start_current_session))
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

        app_state: dict[int, Any] = self.db.load_app_state()
        self.activity_in_timer1: int = app_state['activity_in_timer1']
        self.activity_in_timer2: int = app_state['activity_in_timer2']

        self.running_1: bool = False
        self.running_2: bool = False

    def on_select_combo_1(self, event=None):
        self.activity_in_timer1 = gui.combobox_1.current() + 1  # слева отсчёт с 1, справа -- с 0; 
        gui.time_1_label.config(
            text=sec_to_time(self.durations_of_activities_in_current_session[self.activity_in_timer1])
        )
        if self.running_1 or self.running_2:
            if self.activity_in_timer1 == self.activity_in_timer2:
                self.running_1 = True
                gui.start1_button.config(state=BUTTON_PARAM_STATE_DICT[False])
            else:
                self.running_1 = False
                gui.start1_button.config(state=BUTTON_PARAM_STATE_DICT[True])

    def on_select_combo_2(self, event=None):
        self.activity_in_timer2 = gui.combobox_2.current() + 1
        gui.time_2_label.config(
            text=sec_to_time(self.durations_of_activities_in_current_session[self.activity_in_timer2])
        )
        if self.running_1 or self.running_2:
            if self.activity_in_timer2 == self.activity_in_timer1:
                self.running_2 = True
                gui.start2_button.config(state=BUTTON_PARAM_STATE_DICT[False])
            else:
                self.running_2 = False
                gui.start2_button.config(state=BUTTON_PARAM_STATE_DICT[True])

    def start_session(self):
        # print("Начинаем новую сессию...")
        self.is_in_session = True
        self.running_1 = False
        self.running_2 = False
        self.session_number += 1
        for key in self.durations_of_activities_in_current_session:
            self.durations_of_activities_in_current_session[key] = 0
        self.duration_of_all_activities = 0
        self.start_current_session_sec = time.time()
        self.start_current_session = sec_to_datetime(self.start_current_session_sec)
        self.amount_of_subsessions = 0
        self.db.create_new_session(
            self.session_number,
            self.start_current_session,
            self.amount_of_activities
        )
        
        gui.start_sess_datetime_label.config(text=self.start_current_session)
        gui.current_session_value_label.config(text=self.session_number)
        gui.time_1_label.config(text="00:00:00")
        gui.time_2_label.config(text="00:00:00")

    def terminate_session(self, retroactively=False):
        # print("Завершаем сессию")
        self.is_in_session = False
        if self.running_1 or self.running_2:
            self.stop_timers()

        if not retroactively:
            self.end_current_session_sec = time.time()
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
        gui.start1_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        gui.start2_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        gui.stop_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
            
    def update_time(self):
        """
Эта функция вызывает саму себя и работает до тех пор, пока (self.running_1 or self.running_2) == True
        """
        if not (self.running_1 or self.running_2):
            return
        self.durations_of_activities_in_current_session[self.current_activity] += 1
        self.duration_of_all_activities += 1
        if self.running_1:
            gui.time_1_label.config(
                text=sec_to_time(self.durations_of_activities_in_current_session[self.activity_in_timer1])
            )
        if self.running_2:
            gui.time_2_label.config(
                text=sec_to_time(self.durations_of_activities_in_current_session[self.activity_in_timer2])
            )

        self.timer_until_the_next_stop += 1
        gui.root.after(
            int(1000*(1 + self.start_timer_time + self.timer_until_the_next_stop - time.perf_counter())),
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
        self.start_timer_time = time.perf_counter()
        self.timer_until_the_next_stop = 0
        # TODO тут правда нужен gui? что-то странно...
        gui.root.after(
            int(1000*(1 + self.start_timer_time + self.timer_until_the_next_stop - time.perf_counter())),
            self.update_time
        )
        # Здесь формулу оставил такой же, как и в методе update_time(): для пущей наглядности
        # Даже не стал убирать нулевой self.timer_until_the_next_stop

    @time_decorator
    def start_timer_1(self):
        """
Запускается при нажатии на кнопку "Старт 1"
        """
        if self.running_1:
            return
        self.running_1 = True
        if not self.running_2:          # если другой таймер стоял (т.е. оба таймера стояли; старт с "нуля")
            self.current_activity: int = self.activity_in_timer1
            if self.activity_in_timer2 == self.activity_in_timer1:
                self.running_2 = True
                gui.start2_button.config(state=BUTTON_PARAM_STATE_DICT[False])
            threading.Thread(target=self.update_time_starting, daemon=True).start()
        else:                           # если другой таймер шёл (т.е. происходит переключение таймера)
            self.ending_subsession()
            self.running_2 = False
            self.current_activity: int = self.activity_in_timer1
        self.start_subs_datetime_sec = time.time()
                
        gui.combobox_1.config(state='disabled')
        gui.combobox_2.config(state='readonly')
        gui.time_1_label.config(bg='green')
        gui.time_2_label.config(bg=gui.DEFAULT_WIN_COLOR)
        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[False])

    @time_decorator
    def start_timer_2(self):
        """
Запускается при нажатии на кнопку "Старт 2"
        """
        if self.running_2:
            return        
        self.running_2 = True
        if not self.running_1:          # если другой таймер стоял (т.е. оба таймера стояли; старт с "нуля")
            self.current_activity: int = self.activity_in_timer2
            if self.activity_in_timer1 == self.activity_in_timer2:
                self.running_1 = True
                gui.start1_button.config(state=BUTTON_PARAM_STATE_DICT[False])
            threading.Thread(target=self.update_time_starting, daemon=True).start()
        else:                           # если другой таймер шёл (т.е. происходит переключение таймера)
            self.ending_subsession()
            self.running_1 = False
            self.current_activity: int = self.activity_in_timer2
        self.start_subs_datetime_sec = time.time()
                
        gui.combobox_1.config(state='readonly')
        gui.combobox_2.config(state='disabled')
        gui.time_1_label.config(bg=gui.DEFAULT_WIN_COLOR)
        gui.time_2_label.config(bg='green')
        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[False])

    @time_decorator
    def stop_timers(self):
        """
Запускается при нажатии на кнопку "Стоп"
        """
        if not (self.running_1 or self.running_2):
            return
        self.running_1 = False
        self.running_2 = False
        self.ending_subsession()

        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[True])
        gui.combobox_1.config(state='readonly')
        gui.combobox_2.config(state='readonly')
        gui.start1_button.config(state='normal')
        gui.start2_button.config(state='normal')
        gui.time_1_label.config(bg=gui.DEFAULT_WIN_COLOR)
        gui.time_2_label.config(bg=gui.DEFAULT_WIN_COLOR)

    def ending_subsession(self):
        self.end_subs_datetime_sec = time.time()
        self.subs_duration_sec = self.end_subs_datetime_sec - self.start_subs_datetime_sec
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


if __name__ == "__main__":
    app = ApplicationLogic()
    root = tk.Tk()
    gui = GuiLayer(root, app)
    root.mainloop()