from activities import ActivitiesTable
from session import Session, Subsession
from db_manager import DB


class ApplicationLogic:
    def __init__(self, db: DB):
        self.db = db
        
        self.activities_table: ActivitiesTable = self.db.activities_table
        self.session: Session | None = self.db.get_last_session()
        if self.session is None:  # случай, если у нас ещё не было ни одной сессии (т.е. новая БД)
            self.session = Session()
        elif len(self.session.subsessions) > 0:
            self.session.current_subsession = len(self.session.subsessions) - 1

    def get_duration_table(self) -> dict[int, int]:
        return self.activities_table.get_duration_table(self.session)

    def start_session(self, start_time) -> None:
        self.session = Session(start_time=start_time)
        self.session.id = self.db.add_session(self.session)

    def terminate_session(self, end_time: int) -> int:
        self.session.end_time = end_time
        self.db.update_session(self.session)
        return self.session.duration

    def start_subsession(self, start_time: int, activity_id: int) -> None:
        self.session.subsessions.append(Subsession(start_time=start_time, activity_id=activity_id))
        self.session.current_subsession = len(self.session.subsessions) - 1  # индекс свежедобавленного элемента

    def terminate_subsession(self, end_time: int) -> None:
        self.session.subsessions[self.session.current_subsession].end_time = end_time
        self.db.add_subsession(self.session, self.session.current_subsession)

    def add_subsession_manually(self, start_time: int, end_time: int, activity_id: int) -> None:
        subsession = Subsession(start_time=start_time, end_time=end_time, activity_id=activity_id)
        self.session.subsessions.append(subsession)
        subsession_number = len(self.session.subsessions) - 1  # индекс свежедобавленного элемента
        self.db.add_subsession(self.session, subsession_number)
