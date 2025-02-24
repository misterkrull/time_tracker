import time

from common_functions import (
    duration_to_string,
    time_to_sec,
    time_to_string,
    datetime_to_sec,
)
from db_manager import DB


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
            # TODO нужно только для инициализации. оставляем?
            self.current_session_start_time: int = 0

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
            self.init_to_start_sess_datetime_label: str = (
                start_current_session_datetime
                if self.is_in_session
                else duration_current_session_HMS
            )
            self.current_session_start_time: int = datetime_to_sec(start_current_session_datetime)

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
        self.current_session_start_time: int = int(time.time())
        current_session_start_time_str = time_to_string(self.current_session_start_time)

        self.db.create_new_session(
            self.session_number, current_session_start_time_str, self._activity_count
        )

    def terminate_session(self, end_time: int) -> int:
        self.is_in_session = False
        duration_current_session = end_time - self.current_session_start_time
        duration_current_session_HMS = duration_to_string(duration_current_session)
        self.db.complete_new_session(
            self.session_number,
            time_to_string(end_time),
            duration_current_session_HMS,
        )
        return duration_current_session
