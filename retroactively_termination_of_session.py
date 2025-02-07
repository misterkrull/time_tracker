import time
import tkinter as tk

from common_functions import sec_to_datetime, datetime_to_sec
# from time_tracker import ApplicationLogic  
    # если закольцуется, то можно будет удалить, ибо нужно только ради аннотации

def _get_end_current_session_sec(entered_datetime: str, end_subs_datetime_sec: int) -> int:
    try:
        # TODO подчистить имена переменных в комментах везде в этой функции!!!
        #  - вот тут немного неясно, что за датавремя
        #   upd: понял, зачем. Там далее по коду используется self.app.end_current_session
        #        но я всё-таки решил переделать и не создавать тут self.app.end_current_session
        #        да, потом в terminate_session придётся обратно из секунд в даты конвертировать 
        #           лишний раз -- ну и пусть, не велика беда
        #        зато код становится понятнее
        #        и не надо дробить функцию datetime_to_sec ради этой копеешной оптимизации
        # self.app.end_current_session = \
        #     datetime.strptime(entered_datetime.strip(), '%Y-%m-%d %H:%M:%S')
        end_current_session_sec: int | None = datetime_to_sec(entered_datetime.strip())
    except ValueError:
        raise ValueError("Вы ввели некорректные дату и время")
    # self.app.end_current_session_sec = self.app.end_current_session.timestamp()
    if end_current_session_sec < int(end_subs_datetime_sec):
        # int() сделали потому, что слева по факту целое число, а справа есть ещё дробная часть,
        # которая в итоге не отображается - а нам в итоге только целая часть и нужна
        # в противном случае поведение программы становится немного некорректным
        raise ValueError("Завершение сессии должно быть позже окончания последней подсессии!")
    if end_current_session_sec >= time.time():
        raise ValueError("Завершение сессии должно быть задним числом, т.е. в прошлом, а не в будущем!")
    return end_current_session_sec

class RetroactivelyTerminationOfSession:
    def __init__(self, root: tk.Tk, app):
        self.root = root
        self.app = app

        # создаём диалоговое окно
        self.dialog_window = tk.Toplevel(root)
        # указываем, что наше диалоговое окно -- временное по отношению к родительскому окну
        # в т.ч. это убирает кнопки Свернуть/Развернуть, оставляя только крестик в углу
        self.dialog_window.transient(root)
        # блокируем кнопки родительского окна
        self.dialog_window.grab_set()

        # задаём размеры окна
        width = 450
        height = 140
        # Получаем размеры основного окна - нужно для центрирования нашего окна
        x = root.winfo_x() + (root.winfo_width() // 2) - width // 2
        y = root.winfo_y() + (root.winfo_height() // 2) - height // 2

        self.dialog_window.geometry(f"{width}x{height}+{x}+{y}")   # указываем размеры и центрируем
        self.dialog_window.title("Завершить сессию задним числом")

        self._add_widgets()

        self.dialog_window.bind('<Return>', self._press_enter)
        self.dialog_window.bind('<Escape>', self._on_cancel)
    
    def _add_widgets(self):
        # добавляем надпись
        label = tk.Label(
            self.dialog_window,
            text='Введите "задние" дату и время (в формате YYYY-MM-DD HH:MM:SS)\n'
                 'в промежутке между окончанием последней подсессии\n'
                 f'({sec_to_datetime(self.app.end_subs_datetime_sec)}) и текущим временем:',
            font=("Segoe UI", 10)
        )
        label.pack(pady=2)

        # добавляем поле для ввода
        self.entry = tk.Entry(
            self.dialog_window,
            width=25,
            font=("Segoe UI", 12),
            justify='center'
        )
        self.entry.pack(pady=3)
        self.entry.focus_set()
        self.entry.insert(tk.END, sec_to_datetime(self.app.end_subs_datetime_sec))

        # фрейм для кнопок
        button_frame = tk.Frame(self.dialog_window)
        button_frame.pack(pady=7)

        self.ok_button = tk.Button(
            button_frame,
            text="ОК",
            command=self._on_ok,
            width=12,
            font=("Segoe UI", 10)
        )
        self.ok_button.pack(side=tk.LEFT, padx=10, pady=0)

        self.cancel_button = tk.Button(
            button_frame,
            text="Отмена",
            command=self._on_cancel,
            width=12,
            font=("Segoe UI", 10)
        )
        self.cancel_button.pack(side=tk.LEFT, padx=2, pady=0)

    def _on_ok(self):
        try:
            self.app.end_current_session_sec = _get_end_current_session_sec(
                self.entry.get(), self.app.end_subs_datetime_sec
            )
        except ValueError as err:
            tk.messagebox.showerror("Ошибка", str(err))
            return
        
        self.dialog_window.destroy()
        self.app.startterminate_session(retroactively=True)

    def _on_cancel(self, event=None):
        self.dialog_window.destroy()

    def _press_enter(self, event=None):
        if event.widget == self.entry:  # Если фокус на текстовом поле, то нам нужно действие кнопки "ОК"
            self.ok_button.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки "ОК"
            self.ok_button.after(100, lambda: self.ok_button.config(relief=tk.RAISED))  # Имитируем отпускание кнопки "ОК"
            self.ok_button.invoke()  # Вызываем действие кнопки "ОК"
        else:  # Если фокус не на текстовом поле, т.е. на кнопке "ОК" или на кнопке "Отмена"
            event.widget.config(relief=tk.SUNKEN)  # Имитируем нажатие кнопки
            event.widget.after(100, lambda: event.widget.config(relief=tk.RAISED))  # Имитируем отпускание кнопки
            event.widget.invoke()  # Вызываем действие кнопки, на которой фокус