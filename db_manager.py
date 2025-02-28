import os
import sqlite3

from session import Session
from common_functions import TIMERS, duration_to_string, parse_duration, parse_time, time_to_string

MY_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = "time_tracker.db"
DEFAULT_ACTIVITIES = ["IT", "Английский", "Уборка", "Йога", "Помощь маме"]
DEFAULT_APP_STATE = {f"activity_in_timer{timer}": ("INTEGER", timer) for timer in TIMERS}

# Значение "---" использовалось в старой версии базы для обозначения конца не завершенной сессии
_LEGACY_ZERO_TIME_STRING_VALUE = "---"


def _serialize_session(session: Session) -> tuple[str]:
    return (
        time_to_string(session.start_time),
        time_to_string(session.end_time),
        duration_to_string(session.duration),
        duration_to_string(session.activity_duration_total),
        *[duration_to_string(act_duration) for act_duration in session.activity_durations],
    )


def _deserialize_session(
    id: int,
    start_time_str: str,
    end_time_str: str,
    duration_str: str,
    _amount_of_subsessions: int,
    activity_duration_total_str: str,
    *activity_durations_str: str,
) -> Session:
    start_time = parse_time(start_time_str)
    end_time = (
        parse_time(end_time_str) if end_time_str != _LEGACY_ZERO_TIME_STRING_VALUE else start_time
    )
    session = Session(
        id=id,
        start_time=start_time,
        end_time=end_time,
        activity_durations=list(map(parse_duration, activity_durations_str)),
    )
    if parse_duration(duration_str) != session.duration:
        print(
            "Warning. База данных не в консистентном состоянии!\n"
            f"Длительность сессии {duration_str} "
            f"не совпадает с фактической {duration_to_string(session.duration)}."
        )

    if parse_duration(activity_duration_total_str) != session.activity_duration_total:
        print(
            "Warning. База данных не в консистентном состоянии!\n"
            f"Длительность активностей в сессии {activity_duration_total_str} "
            f"не совпадает с фактической {duration_to_string(session.activity_duration_total)}."
        )

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
                + ", ".join(f"{key} {value[0]}" for key, value in DEFAULT_APP_STATE.items())
                + ")"
            )
            self._cur.execute(
                "INSERT INTO app_state VALUES (" + ", ".join(["?"] * len(DEFAULT_APP_STATE)) + ")",
                [value[1] for value in DEFAULT_APP_STATE.values()],
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

    # да, здесь нужна двойная функция: чтобы сразу два запроса к БД одним махом пульнуть
    # экономия времени существенная! замерял!
    def add_new_subsession_and_update_current_session(
        self,
        current_activity: int,
        start_subs_datetime: str,
        end_subs_datetime: str,
        subs_duration: str,
        session: Session,
        amount_of_subsessions: int,  # TODO выкинуть этот костыль
    ) -> None:
        self._cur.execute(
            "INSERT INTO subsessions VALUES (NULL, ?, ?, ?, ?, ?)",
            (
                session.id,
                current_activity,
                start_subs_datetime,
                end_subs_datetime,
                subs_duration,
            ),
        )
        self.update_session(session, amount_of_subsessions, need_commit=False)
        self._conn.commit()
        # print("В таблицу susbsessions добавили строку: ")
        # print(session_number, current_activity, start_subs_datetime, end_subs_datetime, subs_duration)

    def get_last_session(self) -> Session | None:
        """
        Возвращает последнюю сессию, если таблица sessions не пуста.
        Либо возвращает None, если таблица sessions пуста.
        """
        self._cur.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 1")
        return _deserialize_session(*self._cur.fetchone())

    def write_session(self, session: Session) -> int:
        """Вставляет сессию в базу и возвращает id записи."""

        activities_placeholder = ", ?" * len(session.activity_durations)
        sql_query = f"INSERT INTO sessions VALUES (NULL, ?, ?, ?, 0, ?{activities_placeholder})"
        self._cur.execute(sql_query, _serialize_session(session))
        res = self._cur.lastrowid
        self._conn.commit()
        return res

    def update_session(
        self,
        session: Session,
        amount_of_subsessions: int,  # TODO выкинуть этот ненужный костыль из базы
        need_commit: bool = True,
    ) -> None:
        activities_placeholder = ",".join(
            f"sess_duration_total_act{index + 1} = ?"
            for index in range(len(session.activity_durations))
        )

        self._cur.execute(
            "UPDATE sessions SET "
            "start_sess_datetime = ?,"
            "end_sess_datetime = ?,"
            "sess_duration_total = ?,"
            "sess_duration_total_acts_all = ?,"
            f"{activities_placeholder},"
            "amount_of_subsessions = ?"
            "WHERE id = ?",
            (*_serialize_session(session), amount_of_subsessions, session.id),
        )

        if need_commit:
            self._conn.commit()

    def get_amount_of_subsessions(self, session_number: int) -> int:
        self._cur.execute(
            "SELECT COUNT(*) FROM subsessions WHERE session_number=?", (session_number,)
        )
        return self._cur.fetchall()[0][0]

    def get_activity_count(self) -> int:
        if self._activity_count is None:
            self._cur.execute("SELECT COUNT(*) FROM activities")
            self._activity_count = self._cur.fetchall()[0][0]
        return self._activity_count

    def get_activity_names(self) -> dict[int, str]:
        self._cur.execute("SELECT id, title FROM activities")
        res = {el[0]: el[1] for el in self._cur.fetchall()}
        self._activity_count = len(res)
        return res
        # TODO заменить на dict(self.cur.fetchall()) -- вроде должно сработать, но надо обдумать

    # уже не используемая функция, но пока удалять не буду: вдруг пригодится?..
    # но пока она использовалсь, то Лёша советовал её переназвать (см. в мой блокнотик)
    # думаю, пока функцию оставлю, но если она потребуется, то может будет переделана,
    #   а там и глядишь ещё раз название переделывать придётся :) так что пока оставлю так
    # def get_subsessions_by_session(self, session_number: int) -> list[dict[str, Any]]:
    #     self.cur.execute(
    #         "SELECT activity, subs_duration FROM subsessions WHERE session_number=?",
    #         (session_number,)
    #     )
    #     rows_in_tuples = self.cur.fetchall()
    #     rows_in_dicts = [{'activity': a, 'subs_duration': s_d} for (a, s_d) in rows_in_tuples]
    #     return rows_in_dicts

    def get_datetime_of_last_subsession(self) -> str:
        self._cur.execute("SELECT end_subs_datetime FROM subsessions ORDER BY id DESC LIMIT 1")
        return str(self._cur.fetchall()[0][0])
        # мы тут не проверяем нашу таблицу на пустоту.
        # вообще такого возникнуть не должно: при пустой таблице параметр self.amount_of_subsessions будет равен 0
        # а эта функция вызывается только если этот параметр больше 0

    def load_app_state(self) -> dict[str, int]:
        self._cur.execute("SELECT * FROM app_state")
        res: tuple = self._cur.fetchall()[0]
        return dict(zip(DEFAULT_APP_STATE.keys(), res))

    def save_app_state(self, activity_in_timer: dict[int, int]) -> None:
        self._cur.execute(
            "UPDATE app_state SET "
            + ", ".join(f"{str(key)} = ?" for key in DEFAULT_APP_STATE.keys()),
            tuple(activity_in_timer.values()),
        )
        self._conn.commit()
