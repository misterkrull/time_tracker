import time
import threading
import tkinter
from typing import Callable


class TimeCounter:
    def __init__(self, tk_root: tkinter.Tk, on_tick_function: Callable):
        self._tk_root = tk_root
        self._on_tick_function = on_tick_function
        self._start_time = 0
        self._is_running = False

    def start(self) -> None:
        self._is_running = True
        self._start_time = time.time()
        self._tick()

    def stop(self) -> None:
        self._is_running = False

    def is_running(self):
        return self._is_running

    def _tick(self):
        """
        Эта функция вызывает коллбэк и саму себя через секунду, пока счетчик запущен.
        """
        self._on_tick_function()

        print(
            1000 * (time.time() - self._start_time),
            threading.get_ident(),
        )

        if self._is_running:
            self._tk_root.after(
                # Интервал времени - секунда минус отклонение от реальной секунды.
                ms=int(1000 * (1 - (time.time() - self._start_time) % 1)),
                func=self._tick,
            )

            # Альтернативный вариант с отдельным потоком:
            # threading.Timer(
            #     <интервал в секундах>,
            #     self._tick
            # ).start()
