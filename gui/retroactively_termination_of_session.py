import time
import tkinter as tk

from tkinter import messagebox  # messagebox не импортируется вместе с tkinter: нужно отдельно прописывать
from typing import Callable

from common_functions import time_to_string, parse_time


def _get_end_current_session(entered_datetime: str, end_last_subsession: int) -> int:
    try:
        end_current_session: int | None = parse_time(entered_datetime.strip())
    except ValueError:
        raise ValueError("Вы ввели некорректные дату и время!") from None

    if end_current_session < end_last_subsession:
        raise ValueError("Завершение сессии должно быть не раньше окончания последней подсессии!")

    if end_current_session >= time.time():
        raise ValueError(
            "Завершение сессии должно быть задним числом, т.е. в прошлом, а не в будущем!"
        )

    return end_current_session


class RetroactivelyTerminationOfSession:
    def __init__(self, tk_root: tk.Tk, end_last_subsession: int, startterminate_session: Callable):
        self._end_last_subsession = end_last_subsession
        self._startterminate_session = startterminate_session

        # создаём диалоговое окно
        self._dialog_window = tk.Toplevel(tk_root)
        # указываем, что наше диалоговое окно -- временное по отношению к родительскому окну
        # в т.ч. это убирает кнопки Свернуть/Развернуть, оставляя только крестик в углу
        self._dialog_window.transient(tk_root)
        # блокируем кнопки родительского окна
        self._dialog_window.grab_set()

        # задаём размеры окна
        width = 450
        height = 140
        # задаём расположение окна (используем размеры и расположение родительского окна)
        x = tk_root.winfo_x() + (tk_root.winfo_width() // 2) - width // 2
        y = tk_root.winfo_y() + (tk_root.winfo_height() // 2) - height // 2

        self._dialog_window.geometry(
            f"{width}x{height}+{x}+{y}"
        )  # указываем размеры и расположение
        self._dialog_window.title("Завершить сессию задним числом")  # указываем название окна

        self._add_widgets()  # добавляем все элементы на наше окно

        self._dialog_window.bind("<Return>", self._press_enter)
        self._dialog_window.bind("<Escape>", self._on_cancel)

    def _add_widgets(self) -> None:
        # добавляем надпись
        label = tk.Label(
            self._dialog_window,
            text='Введите "задние" дату и время (в формате YYYY-MM-DD HH:MM:SS)\n'
            "в промежутке между окончанием последней подсессии\n"
            f"({time_to_string(self._end_last_subsession)}) и текущим временем:",
            font=("Segoe UI", 10),
        )
        label.pack(pady=2)

        # добавляем поле для ввода
        self._input_field = tk.Entry(
            self._dialog_window, width=25, font=("Segoe UI", 12), justify="center"
        )
        self._input_field.pack(pady=3)
        self._input_field.focus_set()
        self._input_field.insert(tk.END, time_to_string(self._end_last_subsession))

        # фрейм для кнопок
        button_frame = tk.Frame(self._dialog_window)
        button_frame.pack(pady=7)

        self._ok_button = tk.Button(
            button_frame, text="ОК", command=self._on_ok, width=12, font=("Segoe UI", 10)
        )
        self._ok_button.pack(side=tk.LEFT, padx=10, pady=0)

        self._cancel_button = tk.Button(
            button_frame, text="Отмена", command=self._on_cancel, width=12, font=("Segoe UI", 10)
        )
        self._cancel_button.pack(side=tk.LEFT, padx=2, pady=0)

    def _on_ok(self) -> None:
        try:
            end_current_session = _get_end_current_session(
                self._input_field.get(), self._end_last_subsession
            )
        except ValueError as err:
            messagebox.showerror("Ошибка", str(err))
            return

        self._dialog_window.destroy()
        self._startterminate_session(end_current_session)

    def _on_cancel(self, _: tk.Event | None = None) -> None:
        self._dialog_window.destroy()

    def _press_enter(self, event: tk.Event) -> None:
        if (
            event.widget == self._input_field
        ):  # Если фокус на текстовом поле, то нам нужно действие кнопки "ОК"
            self._ok_button.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки "ОК"
            self._ok_button.after(
                100, lambda: self._ok_button.config(relief=tk.RAISED)
            )  # Имитируем отпускание кнопки "ОК"
            self._ok_button.invoke()  # Вызываем действие кнопки "ОК"
        else:  # Если фокус не на текстовом поле, т.е. на кнопке "ОК" или на кнопке "Отмена"
            event.widget.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки
            event.widget.after(
                100, lambda: event.widget.config(relief=tk.RAISED)
            )  # Имитируем отпускание кнопки
            event.widget.invoke()  # Вызываем действие кнопки, на которой фокус
