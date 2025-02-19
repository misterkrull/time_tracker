import time

from common_functions import sec_to_datetime, sec_to_time
from time_counter import TimeCounter

class Subsession:
    def __init__(self, _time_counter: TimeCounter, app):
        self._time_counter = _time_counter
        self._app = app

        self._start_time = int(time.time())
        self._start_by_inner_timer = self._time_counter.inner_timer
        self._current_activity = self._app.current_activity

    def ending(self):
        duration: int = self._time_counter.inner_timer - self._start_by_inner_timer
        end_time: int = self._start_time + duration

        self._app.amount_of_subsessions += 1

        # да, здесь нужна двойная функция: чтобы сразу два запроса к БД одним махом пульнуть
        # экономия времени существенная! замерял!
        self._app.db.add_new_subsession_and_update_current_session(
            self._app.session_number,
            self._current_activity,
            sec_to_datetime(self._start_time),
            sec_to_datetime(end_time),
            sec_to_time(duration),
            self._app.amount_of_subsessions,
            sec_to_time(self._app.duration_of_all_activities),
            sec_to_time(self._app.durations_of_activities_in_current_session[self._current_activity]),
        )