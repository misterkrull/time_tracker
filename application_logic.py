from dataclasses import InitVar, dataclass, field
import time

from common_functions import (
    duration_to_string,
    parse_duration,
    time_to_string,
    parse_time,
)
from db_manager import DB


@dataclass
class Session:
    id: int = 0
    start_time: int = 0
    duration: int = 0
    activity_durations: list[int] = field(default_factory=list)
    activity_count: InitVar[int] = 0

    def __post_init__(self, activity_count: int):
        if not self.activity_durations:
            self.activity_durations = [0] * activity_count

    @property
    def activity_duration_total(self):
        return sum(self.activity_durations)


class ApplicationLogic:
    def __init__(self):
        self.db = DB()
        # NOTE: тут какая-то дичь, номера активностей считаются с 1, нужно это абстрагировать, чтобы не думать о них
        self.current_activity: int = 1
        self._activity_count: int = self.db.get_activity_count()

        last_session: tuple | None = self.db.get_last_session()
        if last_session is None:  # случай, если у нас ещё не было ни одной сессии (т.е. новая БД)
            self.is_in_session: bool = False
            self.session = Session(activity_count=self._activity_count)

        else:
            self.is_in_session: bool = last_session[2] == "---"
            self.session = Session(
                id=last_session[0],
                start_time=parse_time(last_session[1]),
                duration=parse_duration(last_session[3]),
                activity_durations=list(map(parse_duration, last_session[-self._activity_count :])),
            )

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
        self.is_in_session = True
        self.session = Session(
            id=self.session.id + 1,
            start_time=int(time.time()),
            activity_count=self._activity_count,
        )
        # TODO: сделать нормальную загрузку и сохранение в базу объекта Session целиком
        self.db.create_new_session(
            self.session.id, time_to_string(self.session.start_time), self._activity_count
        )

    def terminate_session(self, end_time: int) -> int:
        self.is_in_session = False
        self.session.duration = end_time - self.session.start_time
        duration_current_session_HMS = duration_to_string(self.session.duration)
        self.db.complete_new_session(
            self.session.id,
            time_to_string(end_time),
            duration_current_session_HMS,
        )
        return self.session.duration
