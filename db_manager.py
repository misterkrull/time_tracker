import os
import sqlite3
from typing import Any

MY_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = "time_tracker.db"


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
            self.cur.execute(
                "INSERT INTO activities VALUES (NULL, 'IT', 0), (NULL, 'Английский', 0);"
            )

        # создаём таблицу sessions
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS sessions "
            "("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "start_sess_datetime DATETIME, "
                "end_sess_datetime DATETIME, "
                "sess_duration_total, "
                "amount_of_subsessions, "
                "sess_duration_total_acts_all, "
                "sess_duration_total_act1 TIME, "
                "sess_duration_total_act2 TIME"
            ")"
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
        
    def add_new_session(
        self, 
        outer_session_number: int,
        start_sess_datetime,
        end_sess_datetime,
        sess_duration_total,
        amount_of_subsessions,
        sess_duration_total_acts_all,
        sess_duration_total_act
    ) -> None:
        #TODO сделать проверку соответствия текущего индекса очереденому primary key: видал, что они расходились
        self.cur.execute(
            "INSERT INTO sessions VALUES (NULL, ?, ?, ?, ?, ?" + ", ?" * len(sess_duration_total_act) + ")",
            (start_sess_datetime, end_sess_datetime, sess_duration_total, 
                amount_of_subsessions, sess_duration_total_acts_all, *list(sess_duration_total_act.values())
            )
        )
        self.conn.commit()
        
    def add_new_subsession(self, session_number: int, activity: int, start_subs_datetime, end_subs_datetime, subs_duration) -> None:
        self.cur.execute(
            "INSERT INTO subsessions VALUES (NULL, ?, ?, ?, ?, ?)",
            (session_number, activity, start_subs_datetime, end_subs_datetime, subs_duration)
        )
        print("В таблицу susbsessions добавили строку: ")
        #TODO сделать проверку соответствия session_number очереденому primary key: видал, что они расходились
        print(session_number, activity, start_subs_datetime, end_subs_datetime, subs_duration)
        self.conn.commit()
        
    def get_amount_of_subsessions(self, session_number: int) -> int:
        self.cur.execute(
            "SELECT * FROM subsessions WHERE session_number=?", (session_number,)
        )
        rows = self.cur.fetchall()
        return len(rows)
        
    def get_activities(self) -> list[Any]:
        self.cur.execute("SELECT id, title FROM activities")
        return {el[0]:el[1] for el in self.cur.fetchall()}

    def get_subsessions_by_session(self, session_number: int) -> list[Any]:
        self.cur.execute(
            "SELECT activity, subs_duration FROM subsessions WHERE session_number=?",
            (session_number,)
        )
        rows_in_tuples = self.cur.fetchall()
        rows_in_dicts = [{'activity': a, 'subs_duration': s_d} for (a, s_d) in rows_in_tuples]
        return rows_in_dicts
        
    def get_datetime_of_last_subsession(self):
        self.cur.execute("SELECT end_subs_datetime FROM subsessions ORDER BY id DESC LIMIT 1")
        return str(self.cur.fetchall()[0][0])
        # мы тут не проверяем нашу таблицу на пустоту. 
        # вообще такого возникнуть не должно: при пустой таблице параметр self.amount_of_subsessions будет равен 0
        # а эта функция вызывается только если этот параметр больше 0