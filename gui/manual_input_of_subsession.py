import enum
import time
import tkinter as tk
from tkinter import messagebox, ttk

from common_functions import datetime_to_sec, duration_to_string, time_to_sec, time_to_string

class CheckStatus(enum.Enum):
    failed = 0
    unchanged = 1
    changed = 2


class ManualInputOfSubsession:
    def __init__(self, tk_root: tk.Tk, activities_names: dict[int, str]):
        self._activities_names = activities_names

        self._start = int(time.time())
        self._duration: int = 0
        self._end = int(time.time())

        self._init_gui(tk_root)
        self._add_widgets()
        self._set_values()

    def _init_gui(self, tk_root: tk.Tk) -> None:
        # создаём диалоговое окно
        self._dialog_window = tk.Toplevel(tk_root)
        # указываем, что наше диалоговое окно -- временное по отношению к родительскому окну
        # в т.ч. это убирает кнопки Свернуть/Развернуть, оставляя только крестик в углу
        self._dialog_window.transient(tk_root)
        # блокируем кнопки родительского окна
        self._dialog_window.grab_set()
        self._dialog_window.resizable(False, False)  # Запрещаем изменение размеров

        # задаём размеры окна
        width = 400
        height = 180
        # задаём расположение окна (используем размеры и расположение родительского окна)
        x = tk_root.winfo_x() + (tk_root.winfo_width() // 2) - width // 2
        y = tk_root.winfo_y() + (tk_root.winfo_height() // 2) - height // 2

        self._dialog_window.geometry(
            f"{width}x{height}+{x}+{y}"
        )  # указываем размеры и расположение
        self._dialog_window.title("Ручной ввод подсессии")  # указываем название окна

        self._dialog_window.bind("<Return>", self._press_enter)
        self._dialog_window.bind("<Escape>", self._exit)

    def _add_widgets(self) -> None:
        # Активность
        self._activity_label = tk.Label(
            self._dialog_window,
            anchor='w',
            text='Активность:', 
            font=("Segoe UI", 10)
        )
        self._activity_label.place(x=45, y=14)

        self._activity_combobox = ttk.Combobox(
            self._dialog_window,
            font=("Segoe UI", 10),
            values=list(self._activities_names.values()),
            state="readonly",
        )
        self._activity_combobox.place(x=180, y=12, width=170)

        # Начало субсесии
        self._start_label = tk.Label(
            self._dialog_window,
            anchor='w',
            text='Начало субсессии:',
            font=("Segoe UI", 10)
        )
        self._start_label.place(x=45, y=44, height=21)

        self._start_input = tk.Entry(
            self._dialog_window,
            font=("Segoe UI", 11)
        )
        self._start_input.place(x=180, y=42, width=170)
        self._start_input.focus_set()
        self._start_input.bind("<FocusOut>", self._check_start)

        # Длительность субсессии
        self._duration_label = tk.Label(
            self._dialog_window,
            text='Длительность субсессии:',
            font=("Segoe UI", 10)
        )
        self._duration_label.place(x=20, y=75, height=21, width=170)

        self._duration_input = tk.Entry(
            self._dialog_window,
            font=("Segoe UI", 11),
            justify="center"
        )
        self._duration_input.place(x=20, y=100, width=170)
        self._duration_input.bind("<FocusOut>", self._check_duration)

        # Конец субсессии
        self._end_label = tk.Label(
            self._dialog_window,
            text='Конец субсессии:',
            font=("Segoe UI", 10)
        )
        self._end_label.place(x=210, y=75, width=170)

        self._end_input = tk.Entry(
            self._dialog_window,
            font=("Segoe UI", 11)
        )
        self._end_input.place(x=210, y=100, width=170)
        self._end_input.bind("<FocusOut>", self._check_end)

        # Кнопка "Добавить субсесиию"
        self._add_button = tk.Button(
            self._dialog_window,
            text='Добавить подсессию',
            font=("Segoe UI", 12),
            command=self._add
        )
        self._add_button.place(x=110, y=133, height=35, width=180)

        # Кнопка "Выход"
        self._exit_button = tk.Button(
            self._dialog_window,
            text='Выход',
            font=("Segoe UI", 10),
            command=self._exit
        )
        self._exit_button.place(x=332, y=145, height=28, width=60)

    def _set_values(self) -> None:
        self._start_input.delete(0, tk.END)
        self._start_input.insert(0, time_to_string(self._start))
        self._duration_input.delete(0, tk.END)
        self._duration_input.insert(0, duration_to_string(self._duration))
        self._end_input.delete(0, tk.END)
        self._end_input.insert(0, time_to_string(self._end))

    # TODO может быть три эти функции объединить?
    def _check_start(self, _: tk.Event | None = None) -> CheckStatus:
        try:
            _start = datetime_to_sec(self._start_input.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Вы ввели некорректные дату и время!")
            self._start_input.focus_set()
            return CheckStatus.failed

        if self._start == _start:
            self._set_values()
            return CheckStatus.unchanged
        else:
            self._start = _start
            self._end = self._start + self._duration
            _blink(self._end_input)
            self._set_values()
            return CheckStatus.changed

    def _check_duration(self, _: tk.Event | None = None) -> CheckStatus:
        try:
            _duration = time_to_sec(self._duration_input.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Вы ввели некорректную длительность!")
            self._duration_input.focus_set()
            return CheckStatus.failed
        
        if _duration < 0:
            messagebox.showerror("Ошибка", "Длительность должна быть больше нуля!")

        if self._duration == _duration:
            self._set_values()
            return CheckStatus.unchanged
        else:
            self._duration = _duration
            self._end = self._start + self._duration
            _blink(self._end_input)
            self._set_values()
            return CheckStatus.changed

    def _check_end(self, _: tk.Event | None = None) -> CheckStatus:
        try:
            _end = datetime_to_sec(self._end_input.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Вы ввели некорректные дату и время!")
            print(self._dialog_window.focus_get())
            self._end_input.focus_set()
            return CheckStatus.failed
        
        if _end < self._start:
            messagebox.showerror("Ошибка", "Конец субсессии должен быть после её начала!")
            self._end_input.focus_set()
            return CheckStatus.failed

        if self._end == _end:
            self._set_values()
            return CheckStatus.unchanged
        else:
            self._end = _end
            self._duration = self._end - self._start
            _blink(self._duration_input)
            self._set_values()
            return CheckStatus.changed

    def _press_enter(self, event: tk.Event) -> None:
        match event.widget:
            case self._start_input:
                check_status = self._check_start()
            case self._duration_input:
                check_status = self._check_duration()
            case self._end_input:
                check_status = self._check_end()
            case _:
                check_status = CheckStatus.unchanged

        if check_status == CheckStatus.unchanged:
            self._add_button.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки
            self._add_button.after(
                100, lambda: self._add_button.config(relief=tk.RAISED)
            )  # Имитируем отпускание кнопки
            self._add()

    def _add(self):
        if self._activity_combobox.current() == -1:
            messagebox.showerror("Ошибка", "Вы не выбрали активность!")
            return
        
    def _exit(self, _: tk.Event | None = None) -> None:
        self._dialog_window.destroy()


def _blink(input_field: tk.Entry) -> None:
    input_field.config(bg='green')
    input_field.after(270, lambda: input_field.config(bg='white'))
