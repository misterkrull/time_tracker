import sqlite3
from pathlib import Path
from typing import Any

from common_functions import duration_to_string, parse_time, time_to_string
from gui.gui_constants import DEFAULT_TIMER_FRAME_COUNT
from session import Session, Subsession


DB_FILENAME = "time_tracker.db"
DEFAULT_ACTIVITIES = ["IT", "Английский", "Уборка", "Йога", "Помощь маме"]

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


def _get_activity_durations(session: Session, activities_count: int) -> list[int]:
    durations_by_activity = [0] * activities_count
    for subs in session.subsessions:
        # TODO: Здесь потенциальный баг, потому что id в базе
        # не обязаны идти по порядку и совпадать с порядковым индексом списка -1,
        # по правильному надо использовать все id из базы и отсортировать их,
        # а еще более правильно вообще не сохранять лишнюю инфу в базе
        durations_by_activity[subs.activity_id - 1] += subs.duration
    return durations_by_activity


def _get_activity_duration_total(session: Session) -> int:
    return sum(map(lambda sub: sub.duration, session.subsessions))


def _session_to_db_data(session: Session, activities_count: int) -> tuple:
    return (
        time_to_string(session.start_time),
        time_to_string(session.end_time),
        # Все что ниже это лишняя инфа, добавляется только для удобного просмотра
        duration_to_string(session.duration),
        len(session.subsessions),
        duration_to_string(_get_activity_duration_total(session)),
        *[duration_to_string(act_duration) for act_duration in _get_activity_durations(session, activities_count)],
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
    def __init__(self, settings: dict[str, Any]):
        self._conn = sqlite3.connect(Path(__file__).absolute().parent / DB_FILENAME)
        self._cur = self._conn.cursor()

        self._timer_frame_count = settings.get('timer_frame_count', DEFAULT_TIMER_FRAME_COUNT)
        self._default_app_state = {
            f"activity_in_timer{num + 1}": num % len(DEFAULT_ACTIVITIES) + 1
            for num in range(self._timer_frame_count)
        }

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
                + ", ".join(f"{field} INTEGER" for field in self._default_app_state)
                + ")"
            )
            self._cur.execute(
                "INSERT INTO app_state VALUES (" + ", ".join("?" * len(self._default_app_state)) + ")",
                list(self._default_app_state.values()),
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
        
        self._cur.execute("SELECT COUNT(*) FROM activities")
        self._activities_count = int(self._cur.fetchone()[0])

    def __del__(self):
        self._conn.close()

    def add_subsession(self, session: Session, subsession_number: int) -> None:
        self._cur.execute(
            "INSERT INTO subsessions VALUES (NULL, ?, ?, ?, ?, ?)",
            (session.id, *_subsession_to_db_data(session.subsessions[subsession_number])),
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
        if session_db_data is None:
            return None
        self._cur.execute(
            "SELECT activity, start_subs_datetime, end_subs_datetime FROM subsessions "
            "WHERE session_number = ?",
            (session_db_data[0],),
        )
        subsession_list_db_data = self._cur.fetchall()
        session = _db_data_to_session(*session_db_data, subsession_list_db_data)
        return session

    def add_session(self, session: Session) -> int:
        """Вставляет сессию в базу (без подсессий) и возвращает id записи."""

        activities_placeholder = ", ?" * self._activities_count
        sql_query = f"INSERT INTO sessions VALUES (NULL, ?, ?, ?, ?, ?{activities_placeholder})"
        self._cur.execute(sql_query, _session_to_db_data(session, self._activities_count))
        res = self._cur.lastrowid
        self._conn.commit()
        return res

    def update_session(
        self,
        session: Session,
        need_commit: bool = True,
    ) -> None:
        activities_placeholder = ",".join(
            f"sess_duration_total_act{index + 1} = ?" for index in range(self._activities_count)
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
            (*_session_to_db_data(session, self._activities_count), session.id),
        )

        if need_commit:
            self._conn.commit()

    def get_activity_table(self) -> dict[int, str]:
        self._cur.execute("SELECT id, title FROM activities")
        activities_table = dict(self._cur.fetchall())
        return activities_table

    def load_all_timers_activity_ids(self) -> list[int]:
        self._cur.execute("SELECT * FROM app_state")
        app_state_table = list(self._cur.fetchall()[0])
        if len(app_state_table) >= self._timer_frame_count:
            return app_state_table[:self._timer_frame_count]
        
        for i in range(len(app_state_table), self._timer_frame_count):
            app_state_table.append(i % self._activities_count + 1)
            self._cur.execute(f"ALTER TABLE app_state ADD COLUMN activity_in_timer{i+1} INTEGER")

        self._cur.execute("UPDATE app_state SET " + ", ".join(
            [f"activity_in_timer{i+1} = '{value}'" for i, value in enumerate(app_state_table)]
        ))
        self._conn.commit()
        return app_state_table

    def save_all_timers_activity_ids(self, activity_ids: list[int]) -> None:
        self._cur.execute(
            "UPDATE app_state SET " + ", ".join(f"{key} = ?" for key in self._default_app_state.keys()),
            activity_ids,
        )
        self._conn.commit()
