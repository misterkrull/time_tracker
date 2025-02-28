import time

from session import Session
from common_functions import parse_time
from db_manager import DB


class ApplicationLogic:
    def __init__(self):
        self.db = DB()
        # NOTE: тут какая-то дичь, номера активностей считаются с 1, нужно это абстрагировать, чтобы не думать о них
        self.current_activity: int = 1
        self._activity_count: int = self.db.get_activity_count()
        self.session: Session | None = self.db.get_last_session()
        if self.session is None:  # случай, если у нас ещё не было ни одной сессии (т.е. новая БД)
            self.session = Session(activity_count=self._activity_count)

        self.amount_of_subsessions: int = self.db.get_amount_of_subsessions(self.session.id)
        # print("Количество подсессий:", self.amount_of_subsessions)
        if self.amount_of_subsessions > 0:
            self.end_last_subsession: int = parse_time(self.db.get_datetime_of_last_subsession())
        # это нужно для работы кнопки "Завершить сессию задним числом"
        # проверка self.amount_of_subsessions > 0 по сути ничего не даёт:
        #   если self.amount_of_subsessions == 0, то у нас кнопка "Задним числом" засерена
        # однако же если у нас ещё ВООБЩЕ не подсессий, то get_datetime_of_last_subsession будет пуст
        # да, тут логичнее было бы проверить количество подсессий во всей таблице subsessions!
        # но у нас такого параметра нет, поэтому проверяем как можем

    def start_session(self) -> None:
        self.session = Session(
            start_time=int(time.time()),
            activity_count=self._activity_count,
        )
        self.session.id = self.db.write_session(self.session)

    def terminate_session(self, end_time: int) -> int:
        self.session.end_time = end_time
        self.db.update_session(self.session, self.amount_of_subsessions)
        return self.session.duration
