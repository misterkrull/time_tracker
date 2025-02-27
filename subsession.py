from common_functions import time_to_string, duration_to_string


class Subsession:
    def __init__(self, start_time: int, app):
        self._start_time = start_time
        self._app = app

        self._current_activity = self._app.current_activity

    def ending(self, duration: int):
        end_time: int = self._start_time + duration
        self._app.amount_of_subsessions += 1
        self._app.session.activity_durations[self._current_activity - 1] += duration
        self._app.end_last_subsession = end_time

        assert self._app.session.id is not None, "session.id is None, возможно сессия не началась"

        # да, здесь нужна двойная функция: чтобы сразу два запроса к БД одним махом пульнуть
        # экономия времени существенная! замерял!
        self._app.db.add_new_subsession_and_update_current_session(
            current_activity=self._current_activity,
            start_subs_datetime=time_to_string(self._start_time),
            end_subs_datetime=time_to_string(end_time),
            subs_duration=duration_to_string(duration),
            session=self._app.session,
            amount_of_subsessions=self._app.amount_of_subsessions,
        )
