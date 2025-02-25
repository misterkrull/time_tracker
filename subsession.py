from common_functions import time_to_string, duration_to_string


class Subsession:
    def __init__(self, start_time: int, app):
        self._start_time = start_time 
        self._app = app 

        self._current_activity = self._app.current_activity

    def ending(self, duration: int):
        end_time: int = self._start_time + duration

        self._app.amount_of_subsessions += 1
        self._app.durations_of_activities_in_current_session[self._current_activity] += duration
        self._app.duration_of_all_activities += duration
        self._app.end_last_subsession = end_time

        # да, здесь нужна двойная функция: чтобы сразу два запроса к БД одним махом пульнуть
        # экономия времени существенная! замерял!
        self._app.db.add_new_subsession_and_update_current_session(
            self._app.session_number,
            self._current_activity,
            time_to_string(self._start_time),
            time_to_string(end_time),
            duration_to_string(duration),
            self._app.amount_of_subsessions,
            duration_to_string(self._app.duration_of_all_activities),
            duration_to_string(
                self._app.durations_of_activities_in_current_session[self._current_activity]
            ),
        )
