import threading
import time
import tkinter as tk

from common_functions import (
    time_decorator,
    sec_to_time,
    time_to_sec,
    sec_to_datetime,
    datetime_to_sec,
    TIMERS,
)
from db_manager import DB
from gui_layer import (
    GuiLayer,
    BUTTON_PARAM_STATE_DICT,
    BUTTON_SESSIONS_DICT,
    START_TEXT_LABEL_DICT,
)


class ApplicationLogic:
    def __init__(self):
        self.db = DB()
        self.current_activity: int = 1
        self.start_subs_datetime_sec: int = 0
        self.start_subs_by_inner_timer: int = 0

        self._activity_count: int = self.db.get_activity_count()

        last_session: tuple | None = self.db.get_last_session()
        if last_session is None:  # случай, если у нас ещё не было ни одной сессии (т.е. новая БД)
            # TODO может быть убрать отсюда те переменные, которые нам будут не нужны?
            # однако если убрать, то эти переменные будут объявлены в другом месте
            #   их там в другом месте надо будет аннотировать? вот вопрос...
            self.is_in_session: bool = False  # ЭТО НУЖНО
            self.session_number: int = 0  # ЭТО НУЖНО
            self.start_current_session: str = "00:00:00"  # это не нужно
            self.start_current_session_sec: int = 0.0  # это не нужно
            self.duration_current_session: str = "--:--:--"  # ЭТО НУЖНО
            self.duration_current_session_sec: int = 0  # это не нужно
            self.durations_of_activities_in_current_session: dict[int, int] = {
                i + 1: 0 for i in range(self._activity_count)
            }  # у нас
        else:
            self.is_in_session: bool = last_session[2] == "---"
            self.session_number: int = last_session[0]
            self.start_current_session: str = last_session[1]
            self.start_current_session_sec: int = datetime_to_sec(self.start_current_session)
            self.duration_current_session: str = last_session[3]
            self.duration_current_session_sec: int = time_to_sec(self.duration_current_session)
            # нам в зависимости от is_in_session нужно будет либо start_current_session,
            #                                                либо duration_current_session
            self.durations_of_activities_in_current_session: dict[int, int] = {
                i + 1: v
                for i, v in enumerate(map(time_to_sec, last_session[-self._activity_count :]))
            }
        self.duration_of_all_activities: int = sum(
            self.durations_of_activities_in_current_session.values()
        )

        self.amount_of_subsessions: int = self.db.get_amount_of_subsessions(self.session_number)
        # print("Количество подсессий:", self.amount_of_subsessions)
        if self.amount_of_subsessions > 0:
            self.end_subs_datetime_sec: int = datetime_to_sec(
                self.db.get_datetime_of_last_subsession()
            )
        # это нужно для работы кнопки "Завершить сессию задним числом"
        # проверка self.amount_of_subsessions > 0 по сути ничего не даёт:
        #   если self.amount_of_subsessions == 0, то у нас кнопка "Задним числом" засерена
        # однако же если у нас ещё ВООБЩЕ не подсессий, то get_datetime_of_last_subsession будет пуст
        # да, тут логичнее было бы проверить количество подсессий во всей таблице subsessions!
        # но у нас такого параметра нет, поэтому проверяем как можем

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
            self.session_number, self.start_current_session, self._activity_count
        )

        gui.start_sess_datetime_label.config(text=self.start_current_session)
        gui.current_session_value_label.config(text=self.session_number)
        for timer in gui.timer_list:
            timer.gui_label.config(text="00:00:00")

    def terminate_session(self, retroactively=False):
        self.is_in_session = False
        self.stop_timers()

        if not retroactively:
            self.end_current_session_sec = int(time.time())
        self.end_current_session = sec_to_datetime(self.end_current_session_sec)
        self.duration_current_session_sec = (
            self.end_current_session_sec - self.start_current_session_sec
        )
        self.duration_current_session = sec_to_time(self.duration_current_session_sec)
        self.db.complete_new_session(
            self.session_number, self.end_current_session, self.duration_current_session
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
        for timer in gui.timer_list:
            timer.gui_start_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        gui.stop_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])

    @time_decorator
    def stop_timers(self):
        """
        Запускается при нажатии на кнопку "Стоп"
        """
        # TODO вот тут мы проверяем по всем таймерам, однако всегда (кроме самого начала до запуска
        #   первого таймера) тут можно использовать self.time_counter.is_running
        #   Может как-то модифицировать, чтобы можно было всегда так делать?
        #   К примеру, добавить в инициализацию TimeCounter необзяательный флаг is_running.
        #       который по умолчанию будет True, но вот для первого раза будет False
        if not any(timer.is_running for timer in gui.timer_list):
            return
        for timer in gui.timer_list:
            timer.is_running = False
        self.time_counter.is_running = False
        self.ending_subsession()

        gui.retroactively_terminate_session_button.config(state=BUTTON_PARAM_STATE_DICT[True])
        for timer in gui.timer_list:
            timer.gui_combobox.config(state="readonly")
            timer.gui_start_button.config(state="normal")
            timer.gui_label.config(bg=gui.DEFAULT_WIN_COLOR)

    def ending_subsession(self):
        self.subs_duration_sec: int = self.time_counter.inner_timer - self.start_subs_by_inner_timer
        self.end_subs_datetime_sec: int = self.start_subs_datetime_sec + self.subs_duration_sec

        # обновляем время старта по inner_timer для следующей подсессии (если она будет)
        self.start_subs_by_inner_timer = self.time_counter.inner_timer

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
            sec_to_time(self.durations_of_activities_in_current_session[self.current_activity]),
        )

        self.start_subs_datetime_sec = start_next_subs_datetime_sec


if __name__ == "__main__":
    app = ApplicationLogic()
    root = tk.Tk()
    gui = GuiLayer(root, app)
    root.mainloop()