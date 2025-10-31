import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from common_functions import duration_to_string, time_to_string
from gui.manual_input_of_subsession_extended import ManualInputOfSubsessionExtended


class ManualInputOfSubsessionSimple:
    def __init__(
        self,
        tk_root: tk.Tk,
        combobox_names: dict[int, str],
        combobox_height: int,
        add_subsession: Callable,
        current_activity: int | None,
        start_current_subsession: int | None,
        end_previous_subsession: int | None
    ):
        self._tk_root = tk_root
        self._combobox_names = combobox_names
        self._combobox_height = combobox_height
        self._add_subsession = add_subsession
        self._current_activity = current_activity
        self._start_current_subsession = start_current_subsession
        self._end_previous_subsession = end_previous_subsession

        if self._start_current_subsession is not None and self._end_previous_subsession is not None:
            self._max_duration = self._start_current_subsession - self._end_previous_subsession
        else:
            self._max_duration = None

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
        y = tk_root.winfo_y() + (tk_root.winfo_height() // 2) - height // 2 + 250

        self._dialog_window.geometry(
            f"{width}x{height}+{x}+{y}"
        )  # указываем размеры и расположение
        self._dialog_window.title("Упрощённый ручной ввод подсессии")  # указываем название окна

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
        self._activity_label.place(x=15, y=14)

        self._activity_combobox = ttk.Combobox(
            self._dialog_window,
            # font=("Segoe UI", 10),  # убрал, т.к. оригинальный шрифт меньше => больше символов влезает в комбобокс
            values=list(self._combobox_names.values()),
            state="readonly",
            height=self._combobox_height
        )
        self._activity_combobox.place(x=180, y=12, width=200)
        self._activity_combobox.bind("<<ComboboxSelected>>", self._combobox_selected)

        # Сколько секунд добавить
        self._duration_label = tk.Label(
            self._dialog_window,
            anchor='w',
            text='Сколько секунд добавить:',
            font=("Segoe UI", 10)
        )
        self._duration_label.place(x=15, y=44, height=21)

        self._duration_input = tk.Entry(
            self._dialog_window,
            font=("Segoe UI", 11)
        )
        self._duration_input.place(x=180, y=42, width=80)
        self._duration_input.focus_set()
        self._duration_input.bind("<Key>", self._validate_numeric_input)

        # (max: )
        self._max_duration_label = tk.Label(
            self._dialog_window,
            anchor='w',
            text='',
            font=("Segoe UI", 10)
        )
        self._max_duration_label.place(x=300, y=44, height=21)

        # Кнопка "Добавить подсесиию"
        self._add_button = tk.Button(
            self._dialog_window,
            text='Добавить подсессию',
            font=("Segoe UI", 12),
            command=self._add,
            state="disabled"
        )
        self._add_button.place(x=110, y=78, height=35, width=180)

        # Кнопка "Расширенный ввод"
        self._extended_input_button = tk.Button(
            self._dialog_window,
            text='Расширенный ввод',
            font=("Segoe UI", 12),
            command=self._extended_input,
        )
        self._extended_input_button.place(x=110, y=123, height=35, width=180)

        # Кнопка "Выход"
        self._exit_button = tk.Button(
            self._dialog_window,
            text='Выход',
            font=("Segoe UI", 10),
            command=self._exit
        )
        self._exit_button.place(x=332, y=145, height=28, width=60)

    def _set_values(self) -> None:
        if self._current_activity is not None:
            self._activity_combobox.current(list(self._combobox_names.keys()).index(self._current_activity))
            self._add_button.config(state="normal")
        if self._max_duration is not None:
            self._max_duration_label.config(text=f'(max: {self._max_duration})')

    def _combobox_selected(self, _: tk.Event | None = None) -> None:
        if self._activity_combobox.current() != -1:
            self._add_button.config(state="normal")
        
    def _validate_numeric_input(self, event: tk.Event) -> None | str:
        # пропускаем управляющие клавиши -- иначе он их блокирует
        if event.keysym in [
            "Left", "Right", "Up", "Down", "Home", "End", "BackSpace", "Delete", "Return", "Tab", "Escape"
        ]:
            return
        # блокируем запрещённые символы
        if event.char not in "1234567890":
            return "break"  # Отменяет ввод символа
        
    def _press_enter(self, _: tk.Event) -> None:
        self._add_button.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки
        self._add_button.after(
            150, lambda: self._add_button.config(relief=tk.RAISED)
        )  # Имитируем отпускание кнопки
        self._add()
            
    def _add(self):
        try:
            self._duration = int(self._duration_input.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Вы не ввели количество секунд")
            return

        self._end = self._start_current_subsession if self._start_current_subsession is not None else time.time()
        self._start = self._end - self._duration

        if messagebox.askokcancel(
            "Создание новой подсессии",
            (
                "Будет создана следующая подсессия:\n"
               f" - активность:     {list(self._combobox_names.values())[self._activity_combobox.current()]}\n"
               f" - начало:            {time_to_string(self._start)}\n"
               f" - длительность: {duration_to_string(self._duration)}\n"
               f" - окончание:     {time_to_string(self._end)}\n"
                "\n"
                "Создаём?"
            )
        ):
            activity_id = list(self._combobox_names.keys())[self._activity_combobox.current()]
            self._add_subsession(self._start, self._end, activity_id)
            self._exit()

    def _extended_input(self) -> None:
        self._exit()
        ManualInputOfSubsessionExtended(
            self._tk_root,
            self._combobox_names,
            self._combobox_height,
            self._add_subsession
        )

    def _exit(self, _: tk.Event | None = None) -> None:
        self._dialog_window.destroy()
