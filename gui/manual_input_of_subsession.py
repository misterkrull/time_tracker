import enum
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from common_functions import datetime_to_sec, duration_to_string, time_to_sec, time_to_string
from gui.gui_constants import BACKGROUND_COLOR

class CheckStatus(enum.Enum):
    failed = 0
    unchanged = 1
    changed = 2

CONVERTION = {
    "start": time_to_string,
    "duration": duration_to_string,
    "end": time_to_string
}


class Field:
    def __init__(
        self,
        parent_window: tk.Toplevel,
        name: str,
        label_text: str,
        pos_y: int,
        init_value: int,
        conversion: Callable[[int], str],
        error_message: str,
        check_input: Callable,
        chosen_radiobutton: str,
        changing_radiobutton: Callable
    ):
        self._label = tk.Label(
            parent_window,
            anchor='w',
            text=label_text,
            font=("Segoe UI", 10)
        )
        self._label.place(x=25, y=pos_y+2, height=21)

        self._input = tk.Entry(
            parent_window,
            font=("Segoe UI", 11),
            justify="center"
        )
        self._input.place(x=185, y=pos_y, width=170)
        self._input.bind("<FocusOut>", check_input)
        self._input.insert(tk.END, conversion(init_value))

        self._radiobutton = tk.Radiobutton(
            parent_window,
            variable = chosen_radiobutton,
            value = name,
            command=changing_radiobutton
        )
        self._radiobutton.place(x=360, y=pos_y+2)

        self.value = init_value

class ManualInputOfSubsession:
    def __init__(self, tk_root: tk.Tk, activities_names: dict[int, str]):
        self._activities_names = activities_names

        self._result: dict[str, int] = {
            "start": int(time.time()),
            "duration": 0,
            "end": int(time.time())
        }
        
        self._data_is_correct: bool = True

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
        self._activity_label.place(x=25, y=14)

        self._activity_combobox = ttk.Combobox(
            self._dialog_window,
            font=("Segoe UI", 10),
            values=list(self._activities_names.values()),
            state="readonly",
        )
        self._activity_combobox.place(x=185, y=12, width=170)

        field: dict[str, Field] = {}
        self._chosen_radiobutton = tk.StringVar()

        field['start'] = Field(
            parent_window=self._dialog_window,
            name='start',
            label_text='Начало субсессии:',
            pos_y=42,
            init_value=int(time.time()),
            conversion=time_to_string,
            error_message="Вы ввели некорректные дату и время!",
            check_input=self._check_input,
            chosen_radiobutton=self._chosen_radiobutton,
            changing_radiobutton=self._changing_radiobutton
        )

        field['duration'] = Field(
            parent_window=self._dialog_window,
            name='duration',
            label_text='Длительность субсессии:',
            pos_y=72,
            init_value=0,
            conversion=duration_to_string,
            error_message="Вы ввели некорректную длительность!",
            check_input=self._check_input,
            chosen_radiobutton=self._chosen_radiobutton,
            changing_radiobutton=self._changing_radiobutton
        )

        field['end'] = Field(
            parent_window=self._dialog_window,
            name='end',
            label_text='Конец субсессии:',
            pos_y=102,
            init_value=int(time.time()),
            conversion=time_to_string,
            error_message="Вы ввели некорректные дату и время!",
            check_input=self._check_input,
            chosen_radiobutton=self._chosen_radiobutton,
            changing_radiobutton=self._changing_radiobutton
        )

        # self._result_input: dict[str, tk.Entry] = {}

        # # Начало субсесии
        # self._start_label = tk.Label(
        #     self._dialog_window,
        #     anchor='w',
        #     text='Начало субсессии:',
        #     font=("Segoe UI", 10)
        # )
        # self._start_label.place(x=25, y=44, height=21)

        # self._result_input['start'] = tk.Entry(
        #     self._dialog_window,
        #     font=("Segoe UI", 11),
        #     justify="center"
        # )
        # self._result_input['start'].place(x=185, y=42, width=170)
        # self._result_input['start'].focus_set()
        # self._result_input['start'].bind("<FocusOut>", self._check_input)

        # # Длительность субсессии
        # self._duration_label = tk.Label(
        #     self._dialog_window,
        #     anchor='w',
        #     text='Длительность субсессии:',
        #     font=("Segoe UI", 10)
        # )
        # self._duration_label.place(x=25, y=74, height=21, width=170)

        # self._result_input['duration'] = tk.Entry(
        #     self._dialog_window,
        #     font=("Segoe UI", 11),
        #     justify="center"
        # )
        # self._result_input['duration'].place(x=185, y=72, width=170)
        # self._result_input['duration'].bind("<FocusOut>", self._check_input)

        # # Конец субсессии
        # self._end_label = tk.Label(
        #     self._dialog_window,
        #     anchor='w',
        #     text='Конец субсессии:',
        #     font=("Segoe UI", 10)
        # )
        # self._end_label.place(x=25, y=104, width=170)

        # self._result_input['end'] = tk.Entry(
        #     self._dialog_window,
        #     font=("Segoe UI", 11),
        #     justify="center"
        # )
        # self._result_input['end'].place(x=185, y=102, width=170)
        # self._result_input['end'].bind("<FocusOut>", self._check_input)

        # # Переключатели
        # self._chosen_radiobutton = tk.StringVar()

        # self._start_radiobutton = tk.Radiobutton(
        #     self._dialog_window,
        #     variable = self._chosen_radiobutton,
        #     value = "start",
        #     command=self._changing_radiobutton
        # )
        # self._start_radiobutton.place(x=360, y=44)

        # self._duration_radiobutton = tk.Radiobutton(
        #     self._dialog_window,
        #     variable = self._chosen_radiobutton,
        #     value = "duration",
        #     command=self._changing_radiobutton
        # )
        # self._duration_radiobutton.place(x=360, y=74)

        # self._end_radiobutton = tk.Radiobutton(
        #     self._dialog_window,
        #     variable = self._chosen_radiobutton,
        #     value = "end",
        #     command=self._changing_radiobutton
        # )
        # self._end_radiobutton.place(x=360, y=104)

        # self._chosen_radiobutton.set('end')

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

    @property
    def _blocked_input(self) -> tk.Entry:
        return self._result_input[self._chosen_radiobutton.get()]
        
    def _changing_radiobutton(self):
        for key in self._result_input:
            self._result_input[key].config(state='normal')
        self._blocked_input.config(state='readonly')
            
    def _update_blocked_input(self):
        match self._key_by_widget(self._blocked_input):
            case 'start':
                self._result["start"] = self._result["end"] - self._result["duration"]
            case 'duration':
                if self._result["start"] > self._result["end"]:
                    raise ValueError("Конец субсессии должен быть позже её начала!")
                self._result["duration"] = self._result["end"] - self._result["start"]
            case 'end':
                self._result["end"] = self._result["start"] + self._result["duration"]
        _blink(self._blocked_input)
        self._set_values()

    def _set_values(self) -> None:
        self._blocked_input.config(state='normal')
        for key in self._result_input:
            self._result_input[key].delete(0, tk.END)
            self._result_input[key].insert(0, CONVERTION[key](self._result[key]))
        self._blocked_input.config(state='readonly')

    def _key_by_widget(self, widget: tk.Entry) -> str:
        for key, widget_ in self._result_input.items():
            if widget_ == widget:
                return key
        raise RuntimeError("Widget is not found")

    def _check_input(self, event: tk.Event | None = None):
        if event.widget == self._blocked_input:
            return

        this_widget = self._key_by_widget(event.widget)
        try:
            if this_widget == "duration":
                _msg = "Вы ввели некорректную длительность!"
                _getted_value: int = time_to_sec(event.widget.get())
                if _getted_value < 0:
                    _msg = "Длительность должна быть больше нуля!"
                    raise ValueError
            else:
                _msg = "Вы ввели некорректные дату и время!"
                _getted_value: int = datetime_to_sec(event.widget.get())
        except ValueError:
            messagebox.showerror("Ошибка", _msg)
            event.widget.focus_set()
            self._data_is_correct = False
            return CheckStatus.failed
        
        if self._result[this_widget] == _getted_value and self._data_is_correct:
            self._set_values()
            return CheckStatus.unchanged
        else:
            self._result[this_widget] = _getted_value
            try:
                self._update_blocked_input()
                return CheckStatus.changed
            except ValueError as err:
                messagebox.showerror("Ошибка", str(err))
                event.widget.focus_set()
                self._data_is_correct = False
                return CheckStatus.failed

    def _press_enter(self, event: tk.Event) -> None:
        pass
        # match event.widget:
        #     case self._result_input['start']:
        #         check_status = self._check_start()
        #     case self._result_input['duration']:
        #         check_status = self._check_duration()
        #     case self._result_input['end']:
        #         check_status = self._check_end()
        #     case _:
        #         check_status = CheckStatus.unchanged

        # if check_status == CheckStatus.unchanged:
        #     self._add_button.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки
        #     self._add_button.after(
        #         100, lambda: self._add_button.config(relief=tk.RAISED)
        #     )  # Имитируем отпускание кнопки
        #     self._add()

    def _add(self):
        if self._activity_combobox.current() == -1:
            messagebox.showerror("Ошибка", "Вы не выбрали активность!")
            return
        
    def _exit(self, _: tk.Event | None = None) -> None:
        self._dialog_window.destroy()


def _blink(input_field: tk.Entry) -> None:
    input_field.config(readonlybackground='green')
    input_field.after(200, lambda: input_field.config(readonlybackground=BACKGROUND_COLOR))
