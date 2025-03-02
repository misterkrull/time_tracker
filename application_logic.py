from session import Session, Subsession
from db_manager import DB


class ApplicationLogic:
    def __init__(self):
        self.db = DB()
        self.activity_table: dict[int, str] = self.db.get_activity_table()
        self.session: Session | None = self.db.get_last_session()
        if self.session is None:  # случай, если у нас ещё не было ни одной сессии (т.е. новая БД)
            self.session = Session()

    def get_duration_table(self):
        return {
            act_id: self.session.get_activity_duration(act_id)
            for act_id in self.activity_table.keys()
        }

    def start_session(self, start_time) -> None:
        self.session = Session(start_time=start_time)
        self.session.id = self.db.add_session(self.session)

    def terminate_session(self, end_time: int) -> int:
        self.session.end_time = end_time
        self.db.update_session(self.session)
        return self.session.duration

    def start_subsession(self, start_time: int, activity_id: int) -> None:
        self.session.subsessions.append(Subsession(start_time=start_time, activity_id=activity_id))

    def terminate_subsession(self, end_time: int) -> None:
        self.session.subsessions[-1].end_time = end_time
        self.db.add_last_subsession(self.session)
