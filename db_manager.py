from collections import defaultdict
import os
import sqlite3

from gui.gui_constants import TIMER_FRAME_COUNT
from session import Session, Subsession
from common_functions import duration_to_string, parse_time, time_to_string

MY_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = "time_tracker.db"
DEFAULT_ACTIVITIES = ["IT", "Английский", "Уборка", "Йога", "Помощь маме"]
DEFAULT_APP_STATE = {
    f"activity_in_timer{num + 1}": num % len(DEFAULT_ACTIVITIES) + 1
    for num in range(TIMER_FRAME_COUNT)
}

# Значение "---" использовалось в старой версии базы для обозначения конца не завершенной сессии
_LEGACY_ZERO_TIME_STRING_VALUE = "---"


def _subsession_to_db_data(subsession: Subsession) -> tuple:
    return (
        subsession.activity_id,
        time_to_string(subsession.start_time),
        time_to_string(subsession.end_time),
        duration_to_string(subsession.duration),
    )


def _db_data_to_subsession(activity_id: int, start_time_str: str, end_time_str: str) -> Subsession:
    return Subsession(
        start_time=parse_time(start_time_str),
        end_time=parse_time(end_time_str),
        activity_id=activity_id,
    )


def _get_activity_durations(session: Session) -> list[int]:
    durations_by_activity = [0] * len(DEFAULT_ACTIVITIES)
    for subs in session.subsessions:
        # TODO: Здесь потенциальный баг, потому что id в базе
        # не обязаны идти по порядку и совпадать с порядковым индексом списка -1,
        # по правильному надо использовать все id из базы и отсортировать их,
        # а еще более правильно вообще не сохранять лишнюю инфу в базе
        durations_by_activity[subs.activity_id - 1] += subs.duration
    return durations_by_activity


def _get_activity_duration_total(session: Session) -> int:
    return sum(map(lambda sub: sub.duration, session.subsessions))


def _session_to_db_data(session: Session) -> tuple:
    return (
        time_to_string(session.start_time),
        time_to_string(session.end_time),
        # Все что ниже это лишняя инфа, добавляется только для удобного просмотра
        duration_to_string(session.duration),
        len(session.subsessions),
        duration_to_string(_get_activity_duration_total(session)),
        *[duration_to_string(act_duration) for act_duration in _get_activity_durations(session)],
    )


def _db_data_to_session(
    id: int,
    start_time_str: str,
    end_time_str: str,
    subsession_db_data_list: list[tuple[int, str, str]],
) -> Session:
    start_time = parse_time(start_time_str)
    end_time = (
        parse_time(end_time_str) if end_time_str != _LEGACY_ZERO_TIME_STRING_VALUE else start_time
    )
    subsessions = [_db_data_to_subsession(*subs_data) for subs_data in subsession_db_data_list]

    session = Session(id=id, start_time=start_time, end_time=end_time, subsessions=subsessions)
    return session


class DB:
    def __init__(self):
        self._conn = sqlite3.connect(os.path.join(MY_PATH, DB_FILENAME))
        self._cur = self._conn.cursor()
        self._activity_count: int = None

        # создаём таблицу activities
        # сперва проверяем, есть ли такая; если нет - создаём и заполняем стартовыми данными
        # именно из-за заполнений стартовыми данными приходится такое городить вместо того,
        #   чтобы написать CREATE TABLE IF NOT EXISTS, как я сделал в следующих таблицах
        self._cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
        if not self._cur.fetchone():
            self._cur.execute(
                "CREATE TABLE activities ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "title TEXT, "
                "parent_activity INTEGER"
                ")"
            )
            values = ", ".join(f"(NULL, '{activity}', 0)" for activity in DEFAULT_ACTIVITIES)
            self._cur.execute(f"INSERT INTO activities VALUES {values}")

        # создаём таблицу app_state
        # тоже приходится городить, т.к. надо заполнить дефолтными значениями
        self._cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_state'")
        if not self._cur.fetchone():
            self._cur.execute(
                "CREATE TABLE app_state ("
                + ", ".join(f"{field} INTEGER" for field in DEFAULT_APP_STATE)
                + ")"
            )
            self._cur.execute(
                "INSERT INTO app_state VALUES (" + ", ".join("?" * len(DEFAULT_APP_STATE)) + ")",
                DEFAULT_APP_STATE.values(),
            )

        # создаём таблицу sessions
        self._cur.execute(
            "CREATE TABLE IF NOT EXISTS sessions ("
            + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            + "start_sess_datetime DATETIME, "
            + "end_sess_datetime DATETIME, "
            + "sess_duration_total TIME, "
            + "amount_of_subsessions INTEGER, "
            + "sess_duration_total_acts_all TIME, "
            + ", ".join(
                f"sess_duration_total_act{i} TIME" for i in range(1, len(DEFAULT_ACTIVITIES) + 1)
            )
            + ")"
        )

        # создаём таблицу subsessions
        self._cur.execute(
            "CREATE TABLE IF NOT EXISTS subsessions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "session_number INTEGER, "
            "activity INTEGER, "
            "start_subs_datetime DATETIME, "
            "end_subs_datetime DATE_TIME, "
            "subs_duration TIME"
            ")"
        )

        self._conn.commit()

    def __del__(self):
        self._conn.close()

    def add_last_subsession(self, session: Session) -> None:
        self._cur.execute(
            "INSERT INTO subsessions VALUES (NULL, ?, ?, ?, ?, ?)",
            (session.id, *_subsession_to_db_data(session.subsessions[-1])),
        )
        self.update_session(session, need_commit=False)
        self._conn.commit()

    def get_last_session(self) -> Session | None:
        """
        Возвращает последнюю сессию, если таблица sessions не пуста.
        Либо возвращает None, если таблица sessions пуста.
        """
        self._cur.execute(
            "SELECT id, start_sess_datetime, end_sess_datetime FROM sessions ORDER BY id DESC LIMIT 1"
        )
        session_db_data = self._cur.fetchone()
        self._cur.execute(
            "SELECT activity, start_subs_datetime, end_subs_datetime FROM subsessions "
            "WHERE session_number = ?",
            (session_db_data[0],),
        )
        subsession_db_data_list = self._cur.fetchall()
        session = _db_data_to_session(*session_db_data, subsession_db_data_list)
        return session

    def add_session(self, session: Session) -> int:
        """Вставляет сессию в базу (без подсессий) и возвращает id записи."""

        activities_placeholder = ", ?" * len(DEFAULT_ACTIVITIES)
        sql_query = f"INSERT INTO sessions VALUES (NULL, ?, ?, ?, ?, ?{activities_placeholder})"
        self._cur.execute(sql_query, _session_to_db_data(session))
        res = self._cur.lastrowid
        self._conn.commit()
        return res

    def update_session(
        self,
        session: Session,
        need_commit: bool = True,
    ) -> None:
        activities_placeholder = ",".join(
            f"sess_duration_total_act{index + 1} = ?" for index in range(len(DEFAULT_ACTIVITIES))
        )

        self._cur.execute(
            "UPDATE sessions SET "
            "start_sess_datetime = ?,"
            "end_sess_datetime = ?,"
            # Все что ниже это ненужная избыточность,
            # добавляется лишь для удобного просмотра базы и никак не используется.
            "sess_duration_total = ?,"
            "amount_of_subsessions = ?,"
            "sess_duration_total_acts_all = ?,"
            f"{activities_placeholder}"
            "WHERE id = ?",
            (*_session_to_db_data(session), session.id),
        )

        if need_commit:
            self._conn.commit()

    def get_activity_table(self) -> dict[int, str]:
        self._cur.execute("SELECT id, title FROM activities")
        return dict(self._cur.fetchall())

    def load_all_timers_activity_ids(self) -> list[int]:
        self._cur.execute("SELECT * FROM app_state")
        return self._cur.fetchall()[0]

    def save_all_timers_activity_ids(self, activity_ids: list[int]) -> None:
        self._cur.execute(
            "UPDATE app_state SET " + ", ".join(f"{key} = ?" for key in DEFAULT_APP_STATE.keys()),
            activity_ids,
        )
        self._conn.commit()
