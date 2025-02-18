import time
import tkinter as tk
import threading

from common_functions import sec_to_time

class TimeCounter:
    def __init__(self, gui_layer):
        self._gui_layer = gui_layer

        self._start_inner_timer: float = time.perf_counter()
        self.inner_timer: int = 0  # переименовать: счётчик ходов? seconds_counter?
        self.is_running = True

        self._gui_layer.root.after(
            int(1000 * (1 + self._start_inner_timer + self.inner_timer - time.perf_counter())),
            self.update_time
        )
        # Здесь формулу оставил такой же, как и в методе update_time(): для пущей наглядности
        # Даже не стал убирать нулевой self.timer_until_the_next_stop

    def update_time(self):
        if not self.is_running:
            return
        
        print(
            1000 * (-self._start_inner_timer + time.perf_counter()),
            threading.get_ident(),
        )

        self._gui_layer.app.durations_of_activities_in_current_session[self._gui_layer.app.current_activity] += 1
        self._gui_layer.app.duration_of_all_activities += 1
        
        for timer in self._gui_layer.timer_list:
            if timer.is_running:
                timer.gui_label.config(
                    text=sec_to_time(
                        self._gui_layer.app.durations_of_activities_in_current_session[
                            timer.activity_number
                        ]
                    )
                )

        self.inner_timer += 1

        self._gui_layer.root.after(
            int(1000 * (1 + self._start_inner_timer + self.inner_timer - time.perf_counter())),
            self.update_time
        )
        # Комментарий к данному куску кода:
        # Тут мы вычисляем задержку в миллисекундах по какой-то не очень очевидной формуле, которую
        #   я вывел математически и уже не помню, как именно это было (что-то с чем-то сократилось etc)
        # Но факт в том: эксперимент показал, что эта формула обеспечивает посекундную синхронность
        #   моего таймера и системных часов с точностью примерно 20мс, из-за чего не происходит
        #   накопления ошибки
        # Для пущей точности я НЕ выделяю эту формулу в отдельную переменную, т.к. имеет смысл максимально
        #   сблизить момент вычисления time.perf_counter() и передачу вычисленной задержки в gui.root.after
        # По этой же причине time.perf_counter() стоит в самом конце формулы. Небольшая, но красивая оптимизация
