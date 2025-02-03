import os
import sqlite3
from typing import Any

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
    "is_in_session": 0,
    "activity_in_timer1": 1,
    "activity_in_timer2": 2,
    "start_current_session_sec" : 0.0
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
                    "parent_activity INTEGER, "
                    "duration_in_current_session INTEGER"
                ")"
            )
            values = ", ".join(
                f"(NULL, '{activity}', 0, 0)" for activity in DEFAULT_ACTIVITIES
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
                "CREATE TABLE app_state "
                "("
                    "key TEXT PRIMARY KEY, "
                    "word TEXT"
                ")"
            )
            values = ", ".join(
                f"('{key}', '{word}')" for (key, word) in DEFAULT_APP_STATE.items()
            )
            self.cur.execute(
                f"INSERT INTO app_state VALUES {values};"
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

    def get_subsessions_by_session(self, session_number: int) -> list[dict[str, Any]]:
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

    def initialize_from_db(self) -> dict[str, Any]:
        """
Получение из БД данных, нужных для начала работы приложения
Результат выдаётся в виде словаря с полями:
    is_in_session                   bool            из таблицы app_state
    activity_in_timer1              int             из таблицы app_state
    activity_in_timer2              int             из таблицы app_state
    start_current_session_sec       float           из таблицы app_state

    durations_of_activities_in_current_session
                                    dict[int, int]  два столбца таблицы activities
    amount_of_activities            int             кол-во записей таблицы activities 
    session_number                  int             если is_in_session, то - колво записей в sessions +1;
                                                        иначе - то же без +1
    duration_current_session_sec    int             нужно для того, чтобы отобразить длительность 
                                                        последней завершённой сессии
                                                        (если открываем приложение и там завершённая сессия)
                                                    если is_in_session, то - 0.0
                                                    иначе - поле sess_duration_total последней записи в sessions,
                                                        конвертированное в секунды
        """
        result = {}

        # получаем поля is_in_session, activity_in_timer1, activity_in_timer2 и start_current_session_sec
        self.cur.execute("SELECT key, word FROM app_state;")
        app_state_dict = dict(self.cur.fetchall())
        result['is_in_session'] = bool(int(app_state_dict['is_in_session']))
            # тут нужна конвертация в int, ибо bool('0') = True, а вот bool(int('0')) = False
        result['activity_in_timer1'] = int(app_state_dict['activity_in_timer1'])
        result['activity_in_timer2'] = int(app_state_dict['activity_in_timer2'])
        result['start_current_session_sec'] = float(app_state_dict['start_current_session_sec'])
        
        # получаем поля durations_of_activities_in_current_session и amount_of_activities
        self.cur.execute("SELECT id, duration_in_current_session FROM activities")
        result['durations_of_activities_in_current_session'] = dict(self.cur.fetchall())
        result['amount_of_activities'] = len(result['durations_of_activities_in_current_session'])

        # получаем поля session_number и duration_current_session_sec
        self.cur.execute(
            "SELECT id, sess_duration_total FROM sessions "
            "ORDER BY id DESC LIMIT 1;"
        )
        last_session = self.cur.fetchone()
        if last_session == None:
            last_id, last_sess_duration_total = 0, "00:00:00"  # когда в таблице sessions ни одной записи
        else:
            last_id, last_sess_duration_total = last_session  # когда есть записи
        if result['is_in_session']:
            result['duration_current_session_sec'] = 0.0
            result['session_number'] = last_id + 1
        else:
            hours, minutes, seconds = map(int, last_sess_duration_total.split(':'))
            result['duration_current_session_sec'] = float(3600 * hours + 60 * minutes + seconds)
            result['session_number'] = last_id

        return result

    # TODO переименовать эту функцию: мы ведь не только таблицу app_state меняем...
    # TODO да и таблица app_state не совсем соответствует названию: состояние приложения хранится ещё и в другой таблице...
    def update_app_state(
        self,
        is_in_session: bool,
        activity_in_timer1: int,
        activity_in_timer2: int,
        start_current_session_sec: float,
        durations_of_activities_in_current_session: dict[int, int]
    ) -> None:
        self.cur.execute(
            "UPDATE app_state SET word = CASE "
                f"WHEN key = 'is_in_session' THEN {int(is_in_session)} "  
                    # bool нужно конвертировать в int, ибо в таблице он станет str, 
                    # а bool(str(False)) = True, что никуда не годится
                    # а вот bool(str(int(False))) = False, что хорошо
                f"WHEN key = 'activity_in_timer1' THEN {activity_in_timer1} "
                f"WHEN key = 'activity_in_timer2' THEN {activity_in_timer2} "
                f"WHEN key = 'start_current_session_sec' THEN {start_current_session_sec} "
            "END;"
        )
        
        sql_query = "UPDATE activities SET duration_in_current_session = CASE "
        for (k, w) in durations_of_activities_in_current_session.items():
            sql_query += f"WHEN id = {k} THEN {w} "
        sql_query += "END;"

        self.cur.execute(sql_query)
        self.conn.commit()
