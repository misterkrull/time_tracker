import time
import threading
import tkinter
from typing import Callable


class TimeCounter:
    def __init__(self, tk_root: tkinter.Tk, on_tick_function: Callable):
        self._tk_root = tk_root
        self._on_tick_function = on_tick_function
        self._start_time = None
        self._is_running = False
        self._tkinter_task_id = None
        self._seconds = 0

    def start(self) -> int:
        """
        Запускает time_counter
        Возвращает время его старта (в int)
        """
        self._start_time = time.time()
        self._seconds = 0
        self._start_tick()
        return int(self._start_time)

    def stop(self) -> int:
        """
        Останавливает time_counter
        Возвращает время останова.
        """
        self._tk_root.after_cancel(self._tkinter_task_id)
        self._tkinter_task_id = None
        return int(self._start_time + self._seconds)

    def is_running(self):
        return self._tkinter_task_id is not None

    def _start_tick(self):
        self._tkinter_task_id = self._tk_root.after(
            # Интервал времени:
            # когда пересидели, то секунда минус отклонение;
            # когда не досидели, то секунда плюс отклонение.
            ms=int(1000 * (1 - (time.time() - self._start_time - self._seconds))),
            func=self._tick,
        )

    def _tick(self):
        # print(
        #     1000 * (time.time() - self._start_time),
        #     threading.get_ident(),
        # )
        self._seconds += 1
        self._on_tick_function(self._seconds)
        self._start_tick()
