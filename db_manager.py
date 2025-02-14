import os
import sqlite3

from common_functions import TIMERS

MY_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = "time_tracker.db"
DEFAULT_ACTIVITIES = ["IT", "Английский", "Уборка", "Йога", "Помощь маме"]
DEFAULT_APP_STATE = {f"activity_in_timer{timer}": ("INTEGER", timer) for timer in TIMERS}


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

    def complete_new_session(
        self,
        session_number: int,
        end_sess_datetime: str,
        sess_duration_total: str,
    ) -> None:
        self._cur.execute(
            "UPDATE sessions SET end_sess_datetime = ?, sess_duration_total = ? WHERE id = ?",
            (end_sess_datetime, sess_duration_total, session_number),
        )
        self._conn.commit()

    # да, здесь нужна двойная функция: чтобы сразу два запроса к БД одним махом пульнуть
    # экономия времени существенная! замерял!
    def add_new_subsession_and_update_current_session(
        self,
        session_number: int,
        current_activity: int,
        start_subs_datetime: str,
        end_subs_datetime: str,
        subs_duration: str,
        amount_of_subsessions: int,
        sess_duration_total_acts_all: str,
        sess_duration_total_act_sessnum: str,
    ) -> None:
        self._cur.execute(
            "INSERT INTO subsessions VALUES (NULL, ?, ?, ?, ?, ?)",
            (
                session_number,
                current_activity,
                start_subs_datetime,
                end_subs_datetime,
                subs_duration,
            ),
        )
        # TODO сделать проверку соответствия session_number очереденому primary key: видал, что они расходились
        self._cur.execute(
            "UPDATE sessions SET "
            + "amount_of_subsessions = ?, "
            + "sess_duration_total_acts_all = ?, "
            + f"sess_duration_total_act{current_activity} = ? "
            + "WHERE id = ?",
            (
                amount_of_subsessions,
                sess_duration_total_acts_all,
                sess_duration_total_act_sessnum,
                session_number,
            ),
        )
        self._conn.commit()
        # print("В таблицу susbsessions добавили строку: ")
        # print(session_number, current_activity, start_subs_datetime, end_subs_datetime, subs_duration)

    # TODO сделать проверку соответствия session_number очередному primary key
    def create_new_session(
        self,
        session_number: int,  # да, вот его наверное как-то надо использовать, чтобы проверить соответствие
        start_current_session: str,
        activity_count: int,  # TODO наверное надо этот параметр из класса DB получать, так логичнее
    ) -> None:
        sql_query = (
            "INSERT INTO sessions VALUES ("
            + "NULL, ?, '---', '00:00:00', 0, '00:00:00', "
            + ", ".join(["'00:00:00'"] * activity_count)
            + ")"
        )
        self._cur.execute(sql_query, (start_current_session,))
        self._conn.commit()

        # TODO переделать: сразу сделать SQL-запрос. который считает

    def get_amount_of_subsessions(self, session_number: int) -> int:
        self._cur.execute("SELECT * FROM subsessions WHERE session_number=?", (session_number,))
        rows = self._cur.fetchall()
        return len(rows)

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

    def get_last_session(self) -> tuple | None:
        """
        Возвращает последнюю запись в таблице sessions, если таблица sessions не пуста
        Либо возвращает None, если таблица sessions пуста
        """
        self._cur.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 1")
        return self._cur.fetchone()

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
