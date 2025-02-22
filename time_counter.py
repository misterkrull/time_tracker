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

    def start(self) -> None:
        self._start_time = time.time()
        self._start_tick()

    def stop(self) -> None:
        self._tk_root.after_cancel(self._tkinter_task_id)
        self._tkinter_task_id = None

    def is_running(self):
        return self._tkinter_task_id is not None

    def _start_tick(self):
        self._tkinter_task_id = self._tk_root.after(
            # Интервал времени - секунда минус отклонение от реальной секунды.
            ms=int(1000 * (1 - (time.time() - self._start_time) % 1)),
            func=self._tick,
        )

        # Альтернативный вариант с отдельным потоком:
        # threading.Timer(
        #     <интервал в секундах>,
        #     self._tick
        # ).start()

    def _tick(self):
        print(
            1000 * (time.time() - self._start_time),
            threading.get_ident(),
        )

        self._on_tick_function()
        self._start_tick()
