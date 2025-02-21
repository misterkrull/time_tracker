import time
import tkinter as tk

from common_functions import (
    sec_to_time,
    time_to_sec,
    sec_to_datetime,
    datetime_to_sec,
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
        self.current_activity: int = 0
        self._activity_count: int = self.db.get_activity_count()

        last_session: tuple | None = self.db.get_last_session()
        if last_session is None:  # случай, если у нас ещё не было ни одной сессии (т.е. новая БД)
            self.is_in_session: bool = False
            self.session_number: int = 0
            
            self.init_to_start_sess_datetime_label: str = "--:--:--"
            self._start_current_session: int = 0  # TODO нужно только для инициализации. оставляем?

            self.durations_of_activities_in_current_session: dict[int, int] = {
                i + 1: 0 for i in range(self._activity_count)
            }

        else:
            self.is_in_session: bool = last_session[2] == "---"
            self.session_number: int = last_session[0]

            # NOTE эти две переменные нужны для читаемости текста, а то last_session[1/3] не очень понятно
            # TODO может быть всё-таки их удалить? может last_session сделать словарём?
            start_current_session_datetime: str = last_session[1]
            duration_current_session_HMS: str = last_session[3]
            self.init_to_start_sess_datetime_label: str = \
                start_current_session_datetime if self.is_in_session else duration_current_session_HMS
            self._start_current_session: int = datetime_to_sec(start_current_session_datetime)

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
            self.end_last_subsession: int = datetime_to_sec(
                self.db.get_datetime_of_last_subsession()
            )
        # это нужно для работы кнопки "Завершить сессию задним числом"
        # проверка self.amount_of_subsessions > 0 по сути ничего не даёт:
        #   если self.amount_of_subsessions == 0, то у нас кнопка "Задним числом" засерена
        # однако же если у нас ещё ВООБЩЕ не подсессий, то get_datetime_of_last_subsession будет пуст
        # да, тут логичнее было бы проверить количество подсессий во всей таблице subsessions!
        # но у нас такого параметра нет, поэтому проверяем как можем

    def start_session(self) -> None:
        self.is_in_session = True
        self.session_number += 1
        for activity in self.durations_of_activities_in_current_session.keys():
            self.durations_of_activities_in_current_session[activity] = 0
        self.duration_of_all_activities = 0
        self.amount_of_subsessions = 0
        self._start_current_session: int = int(time.time())
        start_current_session_datetime = sec_to_datetime(self._start_current_session)

        self.db.create_new_session(
            self.session_number, start_current_session_datetime, self._activity_count
        )

        gui.start_sess_datetime_label.config(text=start_current_session_datetime)
        gui.current_session_value_label.config(text=self.session_number)
        for timer in gui.timer_list:
            timer.gui_label.config(text="00:00:00")

    def terminate_session(self, retroactively_end_session: int | None = None) -> None:
        self.is_in_session = False

        if retroactively_end_session is None:
            gui.stop_timers()
            end_current_session = int(time.time())
        else:   
            end_current_session = retroactively_end_session
        duration_current_session = end_current_session - self._start_current_session
        duration_current_session_HMS = sec_to_time(duration_current_session)
        self.db.complete_new_session(
            self.session_number, sec_to_datetime(end_current_session), duration_current_session_HMS
        )

        gui.start_sess_datetime_label.config(text=duration_current_session_HMS)

    def startterminate_session(self, retroactively_end_session: int | None = None) -> None:
        if self.is_in_session:
            self.terminate_session(retroactively_end_session)
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


if __name__ == "__main__":
    app = ApplicationLogic()
    root = tk.Tk()
    gui = GuiLayer(root, app)
    root.mainloop()