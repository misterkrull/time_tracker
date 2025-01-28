from datetime import datetime
import keyboard
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from db_manager import DB
from gui_layer import GuiLayer, BUTTON_PARAM_STATE_DICT, BUTTON_SESSIONS_DICT, START_TEXT_LABEL_DICT

FILENAME_CURRENT = "app_state.txt"

IS_IN_SESSION_DICT = {True: "in_session", False: "not_in_session"}


def time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Функция '{func.__name__}' выполнена за {end_time - start_time:.6f} секунд.")
        return result
    return wrapper
        

class ApplicationLogic:
    def __init__(self):
        self.db = DB()
        try:
            with open(FILENAME_CURRENT, 'r') as file_current:
                self.is_in_session = (file_current.readline().strip() == IS_IN_SESSION_DICT[True])
                self.session_number = int(file_current.readline().strip())
                self.amount_of_activities = int(file_current.readline().strip())
                if self.amount_of_activities != len(self.db.get_activities()):
                    print("Количества активностей в БД и в файле не совпадают!")
                    return
                self.timer_activity = {key: 0 for key in range(1, self.amount_of_activities + 1)}
                for key in self.timer_activity:
                    self.timer_activity[key] = int(file_current.readline().strip())
                self.activity_1 = int(file_current.readline().strip())
                self.activity_2 = int(file_current.readline().strip())
                if self.is_in_session:
                    self.start_current_session_sec = float(file_current.readline().strip())
                    self.start_current_session = \
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_current_session_sec))
                else:
                    self.duration_current_session_sec = float(file_current.readline().strip())
                    if self.duration_current_session_sec == -1.2345:  # специальное значение
                        self.duration_current_session = "--:--:--"
                    else:
                        self.duration_current_session = \
                            time.strftime("%H:%M:%S", time.gmtime(self.duration_current_session_sec))
        except:
            print("Не удалось прочитать из файла, ставим в 0")
            self.is_in_session = False
            self.session_number = 0
            self.amount_of_activities = len(self.db.get_activities())
            self.timer_activity = {key:0 for key in range(1, self.amount_of_activities + 1)}
            for key in self.timer_activity:
                self.timer_activity[key] = 0
            self.activity_1 = 1
            self.activity_2 = 2
            self.duration_current_session_sec = -1.2345  # специальное значение тут создаётся
            self.duration_current_session = "--:--:--"

        self.timer_1 = self.timer_activity[self.activity_1]
        self.timer_2 = self.timer_activity[self.activity_2]
        
        self.activities_dict = self.db.get_activities()
        self.activities_dict_to_show = {k:f"{k}. {v}" for (k, v) in self.activities_dict.items()}
        
        self.amount_of_subsessions = self.db.get_amount_of_subsessions(self.session_number)
        print("Количество подсессий:", self.amount_of_subsessions)
        
        if self.amount_of_subsessions > 0:
            self.end_subs_datetime_sec = datetime.strptime(
                self.db.get_datetime_of_last_subsession(),
                '%Y-%m-%d %H:%M:%S'
            ).timestamp()
            
        self.running = False
        self.running_1 = False
        self.running_2 = False

    def save_current_to_file(self):
        with open(FILENAME_CURRENT, 'w') as file_current:
            text = IS_IN_SESSION_DICT[self.is_in_session] + '\n' + \
                   str(self.session_number) + '\n' + \
                   str(self.amount_of_activities) + '\n'
            for key in self.timer_activity:
                text += str(self.timer_activity[key]) + '\n' 
            text += str(self.activity_1) + '\n' + str(self.activity_2) + '\n'
            if self.is_in_session:
                text += str(self.start_current_session_sec) + '\n'
            else:
                text += str(self.duration_current_session_sec) + '\n'
            file_current.write(text)
    
    def on_select_combo_1(self, event=None):
        self.activity_1 = gui.combobox_1.current() + 1
        gui.time_1_label.config(
            text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_1]))
        )
        if self.running:
            if not self.running_1:
                if self.activity_1 == self.activity_2:
                    self.running_1 = True
                    gui.start1_button.config(state='disabled')
            else:
                self.running_1 = False
                gui.start1_button.config(state='normal')

    def on_select_combo_2(self, event=None):
        self.activity_2 = gui.combobox_2.current() + 1
        gui.time_2_label.config(
            text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_2]))
        )
        if self.running:
            if not self.running_2:
                if self.activity_2 == self.activity_1:
                    self.running_2 = True
                    gui.start2_button.config(state='disabled')
            else:
                self.running_2 = False
                gui.start2_button.config(state='normal')
        
    def start_session(self):
        print("Начинаем новую сессию...")
        self.running = False
        self.running_1 = False
        self.running_2 = False
        self.session_number += 1
        gui.current_session_value_label.config(text=self.session_number)
        for key in self.timer_activity:
            self.timer_activity[key] = 0
        gui.time_1_label.config(text="00:00:00")
        gui.time_2_label.config(text="00:00:00")
        self.start_current_session_sec = time.time()
        self.start_current_session = \
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_current_session_sec))
        self.amount_of_subsessions = 0
        self.save_current_to_file()
        
    def terminate_session(self, retroactively=False):
        print("Завершаем сессию")
        if self.running:
            self.stop_timers()
        if not retroactively:
            self.end_current_session_sec = time.time()
            self.end_current_session = \
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_current_session_sec))
        
        self.duration_current_session_sec = self.end_current_session_sec - self.start_current_session_sec
        self.duration_current_session = \
            time.strftime("%H:%M:%S", time.gmtime(self.duration_current_session_sec))
        
        self.all_subsessions_by_session = self.db.get_subsessions_by_session(self.session_number)
        self.duration_total_act = {key: 0 for key in range(1, self.amount_of_activities + 1)}
        self.duration_total_act_sec = {key: 0 for key in range(1, self.amount_of_activities + 1)}
        for subsession in self.all_subsessions_by_session:
            hours, minutes, seconds = map(int, subsession['subs_duration'].split(':'))
            self.duration_total_act_sec[subsession['activity']] += 3600 * hours + 60 * minutes + seconds
        duration_total_acts_all_sec = 0
        for key in self.duration_total_act:
            self.duration_total_act[key] = \
                time.strftime("%H:%M:%S", time.gmtime(self.duration_total_act_sec[key]))
            duration_total_acts_all_sec += self.duration_total_act_sec[key]
        duration_total_acts_all = \
            time.strftime("%H:%M:%S", time.gmtime(duration_total_acts_all_sec))
        self.db.add_new_session(
            self.session_number,
            self.start_current_session,
            self.end_current_session,
            self.duration_current_session,
            self.amount_of_subsessions,
            duration_total_acts_all,
            self.duration_total_act
        )
        self.save_current_to_file()

    def startterminate_session(self, retroactively=False):
        if self.is_in_session:
            self.terminate_session(retroactively)
            self.is_in_session = False
            gui.start_sess_datetime_label.config(text=self.duration_current_session)
        else:
            self.start_session()
            self.is_in_session = True
            gui.start_sess_datetime_label.config(text=self.start_current_session)
        gui.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[False])
        gui.start1_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        gui.start2_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        gui.stop_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        gui.startterminate_session_button.config(text=BUTTON_SESSIONS_DICT[self.is_in_session])
        gui.start_text_label.config(text=START_TEXT_LABEL_DICT[self.is_in_session])
        self.save_current_to_file()
        
    def retroactively_termination(self):
        # создаём диалоговое окно
        retroactively_termination_dialog = tk.Toplevel(gui.root)
        
        # указываем, что наше диалоговое окно -- временное по отношению к родительскому окну
        # в т.ч. это убирает кнопки Свернуть/Развернуть, оставляя только крестик в углу
        retroactively_termination_dialog.transient(gui.root)
        
        retroactively_termination_dialog.grab_set()   # блокируем кнопки родительского окна
        
        # задаём размеры окна
        width = 450
        height = 140
        
        # Получаем размеры основного окна - нужно для центрирования нашего окна
        x = gui.root.winfo_x() + (gui.root.winfo_width() // 2) - width // 2
        y = gui.root.winfo_y() + (gui.root.winfo_height() // 2) - height // 2
        
        retroactively_termination_dialog.geometry(f"{width}x{height}+{x}+{y}")   # указываем размеры и центрируем
        retroactively_termination_dialog.title("Завершить сессию задним числом")
        
        min_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_subs_datetime_sec))
        
        # добавляем надпись
        label = tk.Label(
            retroactively_termination_dialog,
            text='Введите "задние" дату и время (в формате YYYY-MM-DD HH:MM:SS)\n'
                 'в промежутке между окончанием последней подсессии\n'
                 f'({min_datetime}) и текущим временем:',
            font=("Segoe UI", 10)
        )
        label.pack(pady=2)       
                        
        # добавляем поле для ввода
        entry = tk.Entry(
            retroactively_termination_dialog,
            width=25,
            font=("Segoe UI", 12),
            justify='center'
        )
        entry.pack(pady=3)
        entry.focus_set()
        entry.insert(tk.END, min_datetime)
        
        # фрейм для кнопок
        button_frame = tk.Frame(retroactively_termination_dialog)
        button_frame.pack(pady=7)
        
        def on_ok():
            entered_datetime = entry.get()
            try:
                self.end_current_session = \
                    datetime.strptime(entered_datetime.strip(), '%Y-%m-%d %H:%M:%S')
            except:
                messagebox.showerror("Ошибка", "Вы ввели некорректные дату и время")
            else:
                self.end_current_session_sec = self.end_current_session.timestamp()
                if self.end_current_session_sec < int(self.end_subs_datetime_sec):
                  # int() сделали потому, что по факту целое число, а справа есть ещё дробная часть, 
                  # которая в итоге не отображается - а нам в итоге только целая часть и нужна
                  # в противном случае поведение программы становится немного некорректным
                    messagebox.showerror(
                        "Ошибка",
                        "Завершение сессии должно быть позже окончания последней подсессии!"
                    )
                    return
                if self.end_current_session_sec >= time.time():
                    messagebox.showerror(
                        "Ошибка",
                        "Завершение сессии должно быть задним числом, т.е. в прошлом, а не в будущем!"
                    )
                    return                    
                retroactively_termination_dialog.destroy()
                self.startterminate_session(retroactively=True)                
            
        def on_cancel(event=None):
            retroactively_termination_dialog.destroy()
        
        def on_enter(event=None):
            if event.widget == entry:  # Если фокус на текстовом поле
                ok_button.config(relief=tk.SUNKEN)  # Меняем стиль кнопки на нажатую
                ok_button.after(100, lambda: ok_button.config(relief=tk.RAISED))  # Возвращаем стиль через 100 мс
                on_ok()
            else:
                event.widget.config(relief=tk.SUNKEN)  # Меняем стиль кнопки на нажатую
                event.widget.after(100, lambda: event.widget.config(relief=tk.RAISED))  # Возвращаем стиль через 100 мс
                event.widget.invoke()  # Вызываем действие кнопки, на которой фокус
        
        ok_button = tk.Button(
            button_frame, 
            text="ОК",
            command=on_ok,
            width=12,
            font=("Segoe UI", 10)
        )        
        ok_button.pack(side=tk.LEFT, padx=10, pady=0)

        cancel_button = tk.Button(
            button_frame,
            text="Отмена",
            command=on_cancel,
            width=12,
            font=("Segoe UI", 10)
        )
        cancel_button.pack(side=tk.LEFT, padx=2, pady=0)
        
        retroactively_termination_dialog.bind('<Return>', on_enter)
        retroactively_termination_dialog.bind('<Escape>', on_cancel)
        
    def update_time(self):
        """
Эта функция вызывает саму себя и работает до тех пор, пока self.running==True
        """
        if not self.running: 
            return
        
        if self.working_timer == 1:
            self.timer_activity[self.activity_1] += 1
        if self.working_timer == 2:
            self.timer_activity[self.activity_2] += 1 
        
        if self.running_1:
            gui.time_1_label.config(
                text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_1]))
            )
        if self.running_2:
            gui.time_2_label.config(
                text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_2]))
            )
        
        self.timer_until_the_next_stop += 1           
        gui.root.after(
            int(1000*(1 + self.start_timer_time + self.timer_until_the_next_stop - time.perf_counter())),
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

    def update_time_starting(self):
        """
Стартовая точка вхождения в поток таймера.
Задаёт стартовые переменные и инициирует update_time, которая потом сама себя вызывает
        """
        self.start_timer_time = time.perf_counter()
        self.timer_until_the_next_stop = 0
        gui.root.after(
            int(1000*(1 + self.start_timer_time + self.timer_until_the_next_stop - time.perf_counter())),
            self.update_time
        )
        # Здесь формулу оставил такой же, как и в методе update_time(): для пущей наглядности
        # Даже не стал убирать нулевой self.timer_until_the_next_stop

    def start_timer_1(self):
        """
Запускается при нажатии на кнопку "Старт 1"
        """
        if self.running and self.running_1:
            return
        self.running_1 = True
        self.running_2 = False
        self.working_timer = 1
        gui.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[False])
        if not self.running:
            self.running = True
            self.on_select_combo_2()
            threading.Thread(target=self.update_time_starting, daemon=True).start()
        else:
            self.end_subs_datetime_sec = time.time()
            self.subs_duration = self.end_subs_datetime_sec - self.start_subs_datetime_sec
            self.db.add_new_subsession(
                self.session_number,
                self.current_activity,
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_subs_datetime_sec)),
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_subs_datetime_sec)),
                time.strftime("%H:%M:%S", time.gmtime(self.subs_duration))
            )
            self.amount_of_subsessions += 1
        self.save_current_to_file()
        self.start_subs_datetime_sec = time.time()
        self.current_activity = self.activity_1
        gui.combobox_1.config(state='disabled')
        gui.combobox_2.config(state='readonly')
        gui.time_1_label.config(bg='green')
        gui.time_2_label.config(bg=gui.DEFAULT_WIN_COLOR)

    def start_timer_2(self):
        """
Запускается при нажатии на кнопку "Старт 2"
        """
        if self.running and self.running_2:
            return
        self.running_1 = False
        self.running_2 = True
        self.working_timer = 2
        gui.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[False])
        if not self.running:
            self.running = True
            self.on_select_combo_1()
            threading.Thread(target=self.update_time_starting, daemon=True).start()
        else:
            self.end_subs_datetime_sec = time.time()
            self.subs_duration = self.end_subs_datetime_sec - self.start_subs_datetime_sec
            self.db.add_new_subsession(
                self.session_number,
                self.current_activity,
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_subs_datetime_sec)),
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_subs_datetime_sec)),
                time.strftime("%H:%M:%S", time.gmtime(self.subs_duration))
            )
            self.amount_of_subsessions += 1
        self.save_current_to_file()
        self.start_subs_datetime_sec = time.time()
        self.current_activity = self.activity_2
        gui.combobox_1.config(state='readonly')
        gui.combobox_2.config(state='disabled')
        gui.time_1_label.config(bg=gui.DEFAULT_WIN_COLOR)
        gui.time_2_label.config(bg='green')

    def stop_timers(self):
        """
Запускается при нажатии на кнопку "Стоп"
        """
        if not self.running:
            return
        self.running = False
        self.running_1 = False
        self.running_2 = False
        
        gui.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[True])
        gui.combobox_1.config(state='readonly')
        gui.combobox_2.config(state='readonly')
        gui.start1_button.config(state='normal')
        gui.start2_button.config(state='normal')
        gui.time_1_label.config(bg=gui.DEFAULT_WIN_COLOR)
        gui.time_2_label.config(bg=gui.DEFAULT_WIN_COLOR)
        self.save_current_to_file()

        self.end_subs_datetime_sec = time.time()
        self.subs_duration = self.end_subs_datetime_sec - self.start_subs_datetime_sec
        self.db.add_new_subsession(
            self.session_number,
            self.current_activity,
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_subs_datetime_sec)),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_subs_datetime_sec)),
            time.strftime("%H:%M:%S", time.gmtime(self.subs_duration))
        )
        self.amount_of_subsessions += 1
        print("Количество подсессий:", self.amount_of_subsessions)


if __name__ == "__main__":
    app = ApplicationLogic()
    root = tk.Tk()
    gui = GuiLayer(root, app)
    root.mainloop()