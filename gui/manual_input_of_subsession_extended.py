import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from common_functions import parse_time, duration_to_string, parse_duration, time_to_string


class ManualInputOfSubsessionExtended:
    def __init__(self, tk_root: tk.Tk, combobox_names: dict[int, str], combobox_height: int, add_subsession: Callable):
        self._tk_root = tk_root
        self._combobox_names = combobox_names
        self._combobox_height = combobox_height
        self._add_subsession = add_subsession

        self._start = int(time.time())
        self._duration: int = 0
        self._end = int(time.time())

        self._start_text = time_to_string(self._start)
        self._duration_text = duration_to_string(self._duration)
        self._end_text = time_to_string(self._end)

        self._init_gui(tk_root)
        self._add_widgets()
        self._set_values()

        self._is_changed = False
        self._is_msgbox_called = False
        self._is_force_focus_set = False
        self._is_correct_data = True

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
        self._dialog_window.title("Расширенный ручной ввод подсессии")  # указываем название окна

        self._dialog_window.bind("<Return>", self._press_enter)
        self._dialog_window.bind("<Control-Return>", self._press_ctrl_enter)
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
            # font=("Segoe UI", 10),  # убрал, т.к. оригинальный шрифт меньше => больше символов влезает в комбобокс
            values=list(self._combobox_names.values()),
            state="readonly",
            height=self._combobox_height
        )
        self._activity_combobox.place(x=180, y=12, width=200)
        self._activity_combobox.bind("<<ComboboxSelected>>", self._set_okbutton_state)

        # Начало подсессии
        self._start_label = tk.Label(
            self._dialog_window,
            anchor='w',
            text='Начало подсессии:',
            font=("Segoe UI", 10)
        )
        self._start_label.place(x=45, y=44, height=21)

        self._start_input = tk.Entry(
            self._dialog_window,
            font=("Segoe UI", 11)
        )
        self._start_input.place(x=180, y=42, width=200)
        self._start_input.focus_set()
        self._start_input.bind("<Key>", self._validate_inputing_symbols_startend)
        self._start_input.bind("<FocusOut>", self._check_start)

        # Длительность подсессии
        self._duration_label = tk.Label(
            self._dialog_window,
            text='Длительность подсессии:',
            font=("Segoe UI", 10)
        )
        self._duration_label.place(x=20, y=75, height=21, width=170)

        self._duration_input = tk.Entry(
            self._dialog_window,
            font=("Segoe UI", 11),
            justify="center"
        )
        self._duration_input.place(x=20, y=100, width=170)
        self._duration_input.bind("<Key>", self._validate_inputing_symbols_duration)
        self._duration_input.bind("<FocusOut>", self._check_duration)

        # Конец подсессии
        self._end_label = tk.Label(
            self._dialog_window,
            text='Конец подсессии:',
            font=("Segoe UI", 10)
        )
        self._end_label.place(x=210, y=75, width=170)

        self._end_input = tk.Entry(
            self._dialog_window,
            font=("Segoe UI", 11)
        )
        self._end_input.place(x=210, y=100, width=170)
        self._end_input.bind("<Key>", self._validate_inputing_symbols_startend)
        self._end_input.bind("<FocusOut>", self._check_end)

        # Кнопка "Добавить подсесиию"
        self._add_button = tk.Button(
            self._dialog_window,
            text='Добавить подсессию',
            font=("Segoe UI", 12),
            command=self._add,
            state="disabled"
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
        self._start_text = time_to_string(self._start)
        self._start_input.delete(0, tk.END)
        self._start_input.insert(0, self._start_text)

        self._duration_text = duration_to_string(self._duration)
        self._duration_input.delete(0, tk.END)
        self._duration_input.insert(0, self._duration_text)
        
        self._end_text = time_to_string(self._end)
        self._end_input.delete(0, tk.END)
        self._end_input.insert(0, self._end_text)

    def _validate_inputing_symbols_startend(self, event: tk.Event) -> None | str:
        # пропускаем управляющие клавиши -- иначе он их блокирует
        if event.keysym in [
            "Left", "Right", "Up", "Down", "Home", "End", "BackSpace", "Delete", "Return", "Tab", "Escape"
        ]:
            return
        # блокируем запрещённые символы
        if event.char not in "1234567890:- ":
            return "break"  # Отменяет ввод символа

    def _validate_inputing_symbols_duration(self, event: tk.Event) -> None | str:
        # пропускаем управляющие клавиши -- иначе он их блокирует
        if event.keysym in [
            "Left", "Right", "Up", "Down", "Home", "End", "BackSpace", "Delete", "Return", "Tab", "Escape"
        ]:
            return
        # блокируем запрещённые символы
        if event.char not in "1234567890:":
            return "break"  # Отменяет ввод символа

    def _set_okbutton_state(self, _: tk.Event | None = None) -> None:
        if self._activity_combobox.current() != -1 and self._is_correct_data:
            self._add_button.config(state="normal")

    def _check_start(self, _: tk.Event | None = None) -> None:
        if self._is_msgbox_called:
            return
        if self._is_force_focus_set:
            self._is_force_focus_set = False
            return
        
        try:
            _start_text = self._start_input.get()
            _start = parse_time(_start_text)
        except ValueError:
            self._call_msgbox("Вы ввели некорректные дату и время!")
            self._force_focus_set(self._start_input)
            self._start_text = _start_text
            self._is_changed = True
            self._is_correct_data = False
            return

        self._is_correct_data = True
        self._set_okbutton_state()
        
        if self._start == _start:
            self._set_values()
            if self._start_text == _start_text:
                self._is_changed = False
            else:
                _blink(self._start_input)
                self._is_changed = True
            return
        else:
            self._start = _start
            self._end = self._start + self._duration
            _blink(self._end_input)
            self._set_values()
            self._is_changed = True
            return

    def _check_duration(self, _: tk.Event | None = None) -> None:
        if self._is_msgbox_called:
            return
        if self._is_force_focus_set:
            self._is_force_focus_set = False
            return
        
        try:
            _duration_text = self._duration_input.get()
            _duration = parse_duration(_duration_text)
        except ValueError:
            self._call_msgbox("Вы ввели некорректную длительность!")
            self._force_focus_set(self._duration_input)
            self._duration_text = _duration_text
            self._is_changed = True
            self._is_correct_data = False
            return
                
        self._is_correct_data = True
        self._set_okbutton_state()

        if self._duration == _duration:
            self._set_values()
            if self._duration_text == _duration_text:
                self._is_changed = False
            else:
                _blink(self._duration_input)
                self._is_changed = True
            return
        else:
            self._duration = _duration
            self._end = self._start + self._duration
            _blink(self._end_input)
            self._set_values()
            self._is_changed = True
            return

    def _check_end(self, _: tk.Event | None = None) -> None:
        if self._is_msgbox_called:
            return
        if self._is_force_focus_set:
            self._is_force_focus_set = False
            return
        
        try:
            _end_text = self._end_input.get()
            _end = parse_time(_end_text)
        except ValueError:
            self._call_msgbox("Вы ввели некорректные дату и время!")
            self._force_focus_set(self._end_input)
            self._end_text = _end_text
            self._is_changed = True
            self._is_correct_data = False
            return
        
        if _end < self._start:
            self._end_input.delete(0, tk.END)
            self._end_input.insert(0, time_to_string(_end))
            self._call_msgbox("Конец подсессии должен быть после её начала!")
            self._force_focus_set(self._end_input)
            self._end_text = _end_text
            self._is_changed = True
            self._is_correct_data = False
            return
        
        self._is_correct_data = True
        self._set_okbutton_state()

        if self._end == _end:
            self._set_values()
            if self._end_text == _end_text:
                self._is_changed = False
            else:
                _blink(self._end_input)
                self._is_changed = True
            return
        else:
            self._end = _end
            self._duration = self._end - self._start
            _blink(self._duration_input)
            self._set_values()
            self._is_changed = True
            return
        
    def _call_msgbox(self, text: str) -> None:
        self._add_button.config(state="disabled")

        self._is_msgbox_called = True
        messagebox.showerror("Ошибка", text)
        self._is_msgbox_called = False

    def _force_focus_set(self, entry: tk.Entry) -> None:
        all_inputs = {self._start_input.winfo_name(), self._duration_input.winfo_name(), self._end_input.winfo_name()}
        if self._tk_root.focus_get().winfo_name() in all_inputs:
            if self._tk_root.focus_get().winfo_name() != entry.winfo_name():
                self._is_force_focus_set = True
                entry.focus_set()
        else:
            entry.focus_set()

    def _press_enter(self, event: tk.Event) -> None:
        match event.widget:
            case self._start_input:
                self._check_start()
            case self._duration_input:
                self._check_duration()
            case self._end_input:
                self._check_end()

    def _press_ctrl_enter(self, event: tk.Event) -> None:
        self._press_enter(event)
        if self._is_correct_data and self._activity_combobox.current() != -1:
            self._add_button.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки
            self._add_button.after(
                200, lambda: self._add_button.config(relief=tk.RAISED)
            )  # Имитируем отпускание кнопки
            self._save_subsession()
            
    def _add(self):
        if self._tk_root.focus_get().winfo_name() == self._start_input.winfo_name():
            self._check_start()
        if self._tk_root.focus_get().winfo_name() == self._duration_input.winfo_name():
            self._check_duration()
        if self._tk_root.focus_get().winfo_name() ==  self._end_input.winfo_name():
            self._check_end()
        
        if self._is_correct_data and self._activity_combobox.current() != -1:
            self._save_subsession()

    def _save_subsession(self):
        if messagebox.askokcancel(
            "Создание новой подсессии",
            (
                "Будет создана следующая подсессия:\n"
               f" - активность:     {list(self._combobox_names.values())[self._activity_combobox.current()]}\n"
               f" - начало:            {self._start_text}\n"
               f" - длительность: {self._duration_text}\n"
               f" - окончание:     {self._end_text}\n"
                "\n"
                "Создаём?"
            )
        ):
            activity_id = list(self._combobox_names.keys())[self._activity_combobox.current()]
            self._add_subsession(self._start, self._end, activity_id)

    def _exit(self, _: tk.Event | None = None) -> None:
        self._dialog_window.destroy()


def _blink(input_field: tk.Entry) -> None:
    input_field.config(bg='green')
    input_field.after(270, lambda: input_field.config(bg='white'))
