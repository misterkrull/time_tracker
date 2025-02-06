import os
import sqlite3
from typing import Any

from common_functions import time_decorator, sec_to_time, time_to_sec, sec_to_datetime, datetime_to_sec

MY_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = "time_tracker.db"
DEFAULT_ACTIVITIES = [
    "IT",
    "Английский",
    "Уборка",
    "Йога",
    "Помощь маме"
]
DEFAULT_APP_STATE = {
    "activity_in_timer1": ("INTEGER", 1),
    "activity_in_timer2": ("INTEGER", 2)
}


class DB:
    def __init__(self):
        self.conn = sqlite3.connect(os.path.join(MY_PATH, DB_FILENAME))
        self.cur = self.conn.cursor()

        # создаём таблицу activities
        # сперва проверяем, есть ли такая; если нет - создаём и заполняем стартовыми данными
        # именно из-за заполнений стартовыми данными приходится такое городить вместо того,
        #   чтобы написать CREATE TABLE IF NOT EXISTS, как я сделал в следующих таблицах
        self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='activities'"
        )
        if not self.cur.fetchone():
            self.cur.execute(
                "CREATE TABLE activities "
                "("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "title TEXT, "
                    "parent_activity INTEGER"
                ")"
            )
            values = ", ".join(
                f"(NULL, '{activity}', 0)" for activity in DEFAULT_ACTIVITIES
            )
            self.cur.execute(
                f"INSERT INTO activities VALUES {values};"
            )

        # создаём таблицу app_state
        # тоже приходится городить, т.к. надо заполнить дефолтными значениями
        self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='app_state'"
        )
        if not self.cur.fetchone():
            self.cur.execute(
                "CREATE TABLE app_state (" + \
                    ", ".join(f"{key} {value[0]}" for key, value in DEFAULT_APP_STATE.items()) + \
                ")"
            )
            self.cur.execute(
                "INSERT INTO app_state VALUES (" + \
                    ", ".join(["?"] * len(DEFAULT_APP_STATE)) + \
                ")",
                [value[1] for value in DEFAULT_APP_STATE.values()]
            )

        # создаём таблицу sessions
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS sessions (" + \
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " + \
                "start_sess_datetime DATETIME, " + \
                "end_sess_datetime DATETIME, " + \
                "sess_duration_total TIME, " + \
                "amount_of_subsessions INTEGER, " + \
                "sess_duration_total_acts_all TIME, " + \
                ", ".join(
                    f"sess_duration_total_act{i} TIME" for i in range(1, len(DEFAULT_ACTIVITIES) + 1)
                ) + \
            ");"
        )        

        # создаём таблицу subsessions
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS subsessions "
            "("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "session_number INTEGER, "
                "activity INTEGER, "
                "start_subs_datetime DATETIME, "
                "end_subs_datetime DATE_TIME, "
                "subs_duration TIME"
            ")"
        )

        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def complete_new_session(
        self,
        end_sess_datetime: str,
        sess_duration_total: str,
        session_number: int
    ) -> None:
        self.cur.execute(
            "UPDATE sessions SET end_sess_datetime = ?, sess_duration_total = ? WHERE id = ?",
            (end_sess_datetime, sess_duration_total, session_number)
        )
        self.conn.commit()
            
    def add_new_subsession(
        self, 
        session_number: int, 
        current_activity: int, 
        start_subs_datetime: str, 
        end_subs_datetime: str, 
        subs_duration: str,
        amount_of_subsessions: int,
        sess_duration_total_acts_all: str,
        sess_duration_total_act_sessnum: str
    ) -> None:
        self.cur.execute(
            "INSERT INTO subsessions VALUES (NULL, ?, ?, ?, ?, ?)",
            (session_number, current_activity, start_subs_datetime, end_subs_datetime, subs_duration)
        )
        #TODO сделать проверку соответствия session_number очереденому primary key: видал, что они расходились
        self.cur.execute(
            "UPDATE sessions SET " + \
                "amount_of_subsessions = ?, sess_duration_total_acts_all = ?, " + \
                f"sess_duration_total_act{current_activity} = ? " + \
            "WHERE id = ?",
            (
                amount_of_subsessions,
                sess_duration_total_acts_all,
                sess_duration_total_act_sessnum,
                session_number
            )
        )        
        self.conn.commit()
        # print("В таблицу susbsessions добавили строку: ")
        # print(session_number, current_activity, start_subs_datetime, end_subs_datetime, subs_duration)

    # TODO сделать проверку соответствия session_number очереденому primary key
    def create_new_session(
        self,
        session_number: int,  # да, вот его наверное как-то надо использовать, чтобы проверить соответствие
        start_current_session: str,
        amount_of_activities: int
    ) -> None:
        sql_query = \
            "INSERT INTO sessions VALUES (" + \
                "NULL, ?, '---', '00:00:00', 0, '00:00:00', " + \
                ", ".join(["'00:00:00'"] * amount_of_activities) + \
            ")"
        self.cur.execute(sql_query, (start_current_session,))
        self.conn.commit()
        
        # TODO переделать: сразу сделать SQL-запрос. который считает
    def get_amount_of_subsessions(self, session_number: int) -> int:
        self.cur.execute(
            "SELECT * FROM subsessions WHERE session_number=?", (session_number,)
        )
        rows = self.cur.fetchall()
        return len(rows)
        
    def get_activities(self) -> dict[int, str]:
        self.cur.execute("SELECT id, title FROM activities")
        return {el[0]:el[1] for el in self.cur.fetchall()}
        # TODO заменить на dict(self.cur.fetchall()) -- вроде должно сработать, но надо обдумать

    # уже не используемая функция, но пока удалять не буду: вдруг пригодится?..
    # но пока она использовалсь, то Лёша советовал её переназвать (см. в мой блокнотик)
    # думаю, пока функцию оставлю, но если она потребуется, то может будет переделана, 
    #   а там и глядишь ещё раз название переделывать придётся :) так что пока оставлю так
    def get_subsessions_by_session(self, session_number: int) -> list[dict[str, Any]]:
        self.cur.execute(
            "SELECT activity, subs_duration FROM subsessions WHERE session_number=?",
            (session_number,)
        )
        rows_in_tuples = self.cur.fetchall()
        rows_in_dicts = [{'activity': a, 'subs_duration': s_d} for (a, s_d) in rows_in_tuples]
        return rows_in_dicts
        
    def get_datetime_of_last_subsession(self) -> str:
        self.cur.execute("SELECT end_subs_datetime FROM subsessions ORDER BY id DESC LIMIT 1")
        return str(self.cur.fetchall()[0][0])
        # мы тут не проверяем нашу таблицу на пустоту. 
        # вообще такого возникнуть не должно: при пустой таблице параметр self.amount_of_subsessions будет равен 0
        # а эта функция вызывается только если этот параметр больше 0

    def get_last_session(self) -> tuple | None:
        """
Возвращает последнюю запись в таблице sessions, если таблица sessions не пуста
Либо возвращает None, если таблица sessions пуста
        """
        self.cur.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 1")
        return self.cur.fetchone()

    def load_app_state(self) -> dict[int, Any]:
        self.cur.execute("SELECT * FROM app_state;")
        tupl = self.cur.fetchall()[0]
        return dict(zip(DEFAULT_APP_STATE.keys(), tupl))

    def save_app_state(
        self,
        activity_in_timer1: int,
        activity_in_timer2: int
    ) -> None:
        self.cur.execute(
            "UPDATE app_state SET " + \
                ", ".join(f"{str(key)} = ?" for key in DEFAULT_APP_STATE.keys()),
            (activity_in_timer1, activity_in_timer2)
        )
        self.conn.commit()
