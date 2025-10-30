import sqlite3
from pathlib import Path
from typing import Any

from activities import ActivitiesTable
from common_functions import duration_to_string, parse_time, time_to_string
from filenames import DEFAULT_DB_FILENAME
from session import Session, Subsession

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


def _session_to_db_data(session: Session, activities_table: ActivitiesTable) -> tuple:
    return (
        time_to_string(session.start_time),
        time_to_string(session.end_time),
        # Все что ниже это лишняя инфа, добавляется только для удобного просмотра
        duration_to_string(session.duration),
        session.number_of_subsessions,
        # duration_to_string(session.duration_of_all_subsessions),
        *[duration_to_string(act_duration) for act_duration in activities_table.get_duration_table(session).values()],
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
        db_filename: str = settings.get('db_filename', DEFAULT_DB_FILENAME)
        self._timer_frame_count: int = settings["timer_frame_count"]

        self._conn = sqlite3.connect(Path(__file__).absolute().parent / db_filename)
        self._cur = self._conn.cursor()

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
                + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                + "title TEXT, "
                + "parent_id INTEGER, "
                + "need_show INTEGER, "
                + "order_number REAL"
                + ")"
            )
            values = ", ".join(
                f"(NULL, '{activity}', 0, 1, {float(id) + 1})" for id, activity in enumerate(DEFAULT_ACTIVITIES)
            )
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
        
        self._cur.execute("SELECT id, title, parent_id, need_show, order_number FROM activities")
        self.activities_table = ActivitiesTable(self._cur.fetchall())

    def __del__(self):
        self._conn.close()

    def add_activity(self, title: str, parent_id: int, need_show: bool, order_number: float) -> None:
        self._cur.execute(
            "INSERT INTO activities (title, parent_id, need_show, order_number)"
            "VALUES (?, ?, ?, ?)",
            (title, parent_id, need_show, order_number)
        )
        last_id = self._cur.lastrowid
        new_column_name = f"sess_duration_total_act{last_id}"
        self._cur.execute(
            f"ALTER TABLE sessions ADD COLUMN {new_column_name}"
        )
        self._cur.execute(
            f"UPDATE sessions SET {new_column_name} = '00:00:00'"
        )
        self._conn.commit()

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
        return self.get_session_by_id(self.get_last_session_id())
        
    def get_session_by_id(self, session_id: int) -> Session | None:
        """
        Возращает сессию с указанным id.
        Либо возвращает None, если указанный id не найден в таблице sessions.
        """
        self._cur.execute(
            "SELECT id, start_sess_datetime, end_sess_datetime FROM sessions "
            "WHERE id = ?",
            (session_id,)
        )
        session_db_data = self._cur.fetchone()
        if session_db_data is None:
            return None
        self._cur.execute(
            "SELECT activity, start_subs_datetime, end_subs_datetime FROM subsessions "
            "WHERE session_number = ?",
            (session_id,),
        )
        subsession_list_db_data = self._cur.fetchall()
        session = _db_data_to_session(*session_db_data, subsession_list_db_data)
        return session

    def get_last_session_id(self) -> int | None:
        """
        Возвращает ID последней сессии, если таблица sessions не пуста.
        Либо возвращает None, если таблица sessions пуста.
        """  
        self._cur.execute("SELECT MAX(id) FROM sessions")
        return self._cur.fetchone()[0]

    def add_session(self, session: Session) -> int:
        """Вставляет сессию в базу (без подсессий) и возвращает id записи."""

        sess_duration_total_act_ids = ", ".join(
            f"sess_duration_total_act{id}" for id in self.activities_table.get_all_ids()
        )
        self._cur.execute(
            "INSERT INTO sessions ("
                "start_sess_datetime, "
                "end_sess_datetime, "
                # Все что ниже это ненужная избыточность,
                # добавляется лишь для удобного просмотра базы и никак не используется.
                "sess_duration_total, "
                "amount_of_subsessions, "
                "sess_duration_total_acts_all, "
                f"{sess_duration_total_act_ids}"
            f") VALUES (?, ?, ?, ?, ?, {', '.join(['?'] * self.activities_table.count)})",
            _session_to_db_data(session, self.activities_table),
        )

        res = self._cur.lastrowid
        self._conn.commit()
        return res

    def update_session(
        self,
        session: Session,
        need_commit: bool = True,
    ) -> None:
        activities_placeholder = ", ".join(
            f"sess_duration_total_act{id} = ?" for id in self.activities_table.get_all_ids()
        )

        self._cur.execute(
            "UPDATE sessions SET "
            "start_sess_datetime = ?, "
            "end_sess_datetime = ?, "
            # Все что ниже это ненужная избыточность,
            # добавляется лишь для удобного просмотра базы и никак не используется.
            "sess_duration_total = ?, "
            "amount_of_subsessions = ?, "
            "sess_duration_total_acts_all = ?, "
            f"{activities_placeholder}"
            "WHERE id = ?",
            (*_session_to_db_data(session, self.activities_table), session.id),
        )

        if need_commit:
            self._conn.commit()

    def load_all_timers_activity_ids(self) -> list[int]:
        self._cur.execute("SELECT * FROM app_state")
        app_state_table = list(self._cur.fetchone())

        some_showing_top_level_activity_id = self.activities_table.get_ordered_showing_child_ids(0)[0]
        for timer_id, activity_id in enumerate(app_state_table):
            for id in self.activities_table.get_lineage_ids(activity_id):
                if not self.activities_table._table[id].need_show:
                    app_state_table[timer_id] = some_showing_top_level_activity_id
                    break

        if len(app_state_table) >= self._timer_frame_count:
            return app_state_table[:self._timer_frame_count]
        
        for timer_id in range(len(app_state_table), self._timer_frame_count):
            app_state_table.append(timer_id % self.activities_table.count + 1)
            self._cur.execute(f"ALTER TABLE app_state ADD COLUMN activity_in_timer{timer_id+1} INTEGER")

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
