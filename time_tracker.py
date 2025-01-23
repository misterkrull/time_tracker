from datetime import datetime
import keyboard
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from db_manager import DB

FILENAME_CURRENT = "app_state.txt"

BUTTON_PARAM_STATE_DICT = {True: "normal", False: "disabled"}
BUTTON_SESSIONS_DICT = {True: "Завершить сессию", False: "Новая сессия"}
IS_IN_SESSION_DICT = {True: "in_session", False: "not_in_session"}
START_TEXT_LABEL_DICT = {True: "Началась: ", False: "Длилась: "}


def time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Функция '{func.__name__}' выполнена за {end_time - start_time:.6f} секунд.")
        return result
    return wrapper


class TrackerApp:
    def __init__(self, root):
        self.db = DB()
        try:
            with open(FILENAME_CURRENT, 'r') as file_current:
                self.is_in_session = (file_current.readline().strip() == IS_IN_SESSION_DICT[True])
                self.session_number = int(file_current.readline().strip())
                self.number_of_activities = int(file_current.readline().strip())
                if self.number_of_activities != len(self.db.get_activities()):
                    print("Количества активностей в БД и в файле не совпадают!")
                    return
                self.timer_activity = {key: 0 for key in range(1, self.number_of_activities + 1)}
                for key in self.timer_activity:
                    self.timer_activity[key] = int(file_current.readline().strip())
                self.activity_1 = int(file_current.readline().strip())
                self.activity_2 = int(file_current.readline().strip())
                if self.is_in_session:
                    self.start_current_session_sec = float(file_current.readline().strip())
                    self.start_current_session = time.strftime("%Y-%m-%d %H:%M:%S",
                                                   time.localtime(self.start_current_session_sec))
                else:
                    self.duration_current_session_sec = float(file_current.readline().strip())
                    if self.duration_current_session_sec == -1.2345:  # специальное значение
                        self.duration_current_session = "--:--:--"
                    else:
                        self.duration_current_session = time.strftime("%H:%M:%S",
                                                   time.gmtime(self.duration_current_session_sec))
        except:
            print("Не удалось прочитать из файла, ставим в 0")
            self.is_in_session = False
            self.session_number = 0
            self.number_of_activities = len(self.db.get_activities())
            self.timer_activity = {key:0 for key in range(1, self.number_of_activities + 1)}
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

        #  - - - - ВСЁ ДАЛЬШЕ в __init__ -- ИНТЕРФЕЙС! - - - -    (кроме горячих клавиш, они в самом конце)

        self.root = root
        self.root.title("Мой трекер")
        self.root.geometry("678x250")  # Устанавливаем размер окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # определяем метод закрытия окна
        self.DEFAULT_WIN_COLOR = self.root.cget("background")
        
        # --- ПЕРВАЯ СТРОКА ---
        # Создаем фрейм для первой строки
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=5)

        # Создаем метку для текста "Сессия:"
        self.session_text_label = tk.Label(self.top_frame, text="Сессия:", font=("Helvetica", 14))
        self.session_text_label.pack(side=tk.LEFT)

        # Создаем метку для отображения номера текущей сессии
        self.current_session_value_label = tk.Label(
                                                self.top_frame,
                                                text=self.session_number,
                                                font=("Helvetica", 18)
                                             )
        self.current_session_value_label.pack(side=tk.LEFT, padx=10)  # Отступ между метками

        # Метка для текста "Началась:"/"Длилась:"
        self.start_text_label = tk.Label(self.top_frame,
                                         text=START_TEXT_LABEL_DICT[self.is_in_session],
                                         font=("Helvetica", 14))
        self.start_text_label.pack(side=tk.LEFT, padx=2)

        # Метка для времени начала сессии
        self.start_sess_datetime_label = \
                tk.Label(self.top_frame,
                         text=self.start_current_session if self.is_in_session else self.duration_current_session,
                         font=("Helvetica", 14)
                        )
        self.start_sess_datetime_label.pack(side=tk.LEFT, padx=2)

        # Кнопка "Новая сессия"/"Завершить сессию"
        self.startterminate_session_button = tk.Button(
            self.top_frame,
            font=("Helvetica", 12),
            text=BUTTON_SESSIONS_DICT[self.is_in_session],
            command=self.startterminate_session
        )
        self.startterminate_session_button.pack(side=tk.LEFT, padx=2)  # Отступ между кнопкой и метками
        
        # Кнопка "Задним числом"
        self.retroactively_termination_button = tk.Button(
            self.top_frame,
            font=("Helvetica", 8),
            text="Задним\nчислом",
            state=BUTTON_PARAM_STATE_DICT[self.is_in_session],
            command=self.retroactively_termination
        )
        self.retroactively_termination_button.pack(side=tk.LEFT, padx=4, ipady=0)
        self.retroactively_termination_button.config(
            state=BUTTON_PARAM_STATE_DICT[bool(self.amount_of_subsessions) and self.is_in_session]
        )
        
        # --- ДВЕ ПОЛОВИНЫ ---
        # Создаем фрейм для разделения на две половины
        self.frame = tk.Frame(root)
        self.frame.pack(pady=0)

        # Левая половина
        self.left_frame = tk.Frame(self.frame)
        self.left_frame.pack(side=tk.LEFT, padx=50)

            # Часы 1
        self.time_1_label = tk.Label(
            self.left_frame,
            text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_1])),
            font=("Helvetica", 36)
        )
        self.time_1_label.pack()

            # Комбобокс 1
        self.combobox_1_value = tk.StringVar()
        self.combobox_1 = ttk.Combobox(
            self.left_frame,
            textvariable=self.combobox_1_value,
            values=list(self.activities_dict_to_show.values()),
            state='readonly'
        )
        self.combobox_1.pack(pady=5)
        self.combobox_1_value.set(self.activities_dict_to_show[self.activity_1])
        self.combobox_1.bind("<<ComboboxSelected>>", self.on_select_combo_1)

            # Кнопка "Старт 1"
        self.start1_button = tk.Button(self.left_frame, text="Старт 1", command=self.start_timer_1,
                                       font=("Helvetica", 14), width=10, height=1, 
                                       state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        self.start1_button.pack(pady=5)

        # Правая половина
        self.right_frame = tk.Frame(self.frame)
        self.right_frame.pack(side=tk.RIGHT, padx=50)

            # Часы 2
        self.time_2_label = tk.Label(
            self.right_frame,
            text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_2])),
            font=("Helvetica", 36)
        )
        self.time_2_label.pack()

            # Комбобокс 2
        self.combobox_2_value = tk.StringVar()
        self.combobox_2 = ttk.Combobox(
            self.right_frame,
            textvariable=self.combobox_2_value,
            values=list(self.activities_dict_to_show.values()),
            state='readonly'
        )
        self.combobox_2.pack(pady=5)
        self.combobox_2_value.set(self.activities_dict_to_show[self.activity_2])
        self.combobox_2.bind("<<ComboboxSelected>>", self.on_select_combo_2)

            # Кнопка "Старт 2"
        self.start2_button = tk.Button(self.right_frame, text="Старт 2", command=self.start_timer_2,
                                       font=("Helvetica", 14), width=10, height=1, 
                                       state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        self.start2_button.pack(pady=5)

        # Кнопка "Стоп" внизу
        self.stop_button = tk.Button(root, text="Стоп", command=self.stop_timers,
                                     font=("Helvetica", 14), width=30, height=1, 
                                       state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        self.stop_button.pack(pady=10)
        
        # ГОРЯЧИЕ КЛАВИШИ -  имитируем нажатие нарисованных кнопок
        keyboard.add_hotkey('Alt+F10', self.start1_button.invoke)
        keyboard.add_hotkey('Alt+F11', self.stop_button.invoke)
        keyboard.add_hotkey('Alt+F12', self.start2_button.invoke)


    def save_current_to_file(self):
        with open(FILENAME_CURRENT, 'w') as file_current:
            text = IS_IN_SESSION_DICT[self.is_in_session] + '\n' + \
                   str(self.session_number) + '\n' + \
                   str(self.number_of_activities) + '\n'
            for key in self.timer_activity:
                text += str(self.timer_activity[key]) + '\n' 
            text += str(self.activity_1) + '\n' + str(self.activity_2) + '\n'
            if self.is_in_session:
                text += str(self.start_current_session_sec) + '\n'
            else:
                text += str(self.duration_current_session_sec) + '\n'
            file_current.write(text)
    
    def on_closing(self):
        self.stop_timers()
        self.root.destroy()

    def on_select_combo_1(self, event):
        self.activity_1 = self.combobox_1.current() + 1
        self.time_1_label.config(
            text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_1]))
        )
        if self.running:
           if not self.running_1:
               if self.activity_1 == self.activity_2:
                   self.running_1 = True
                   self.start1_button.config(state='disabled')
           else:
               self.running_1 = False
               self.start1_button.config(state='normal')

    def on_select_combo_2(self, event):
        self.activity_2 = self.combobox_2.current() + 1
        self.time_2_label.config(
            text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_2]))
        )
        if self.running:
           if not self.running_2:
               if self.activity_2 == self.activity_1:
                   self.running_2 = True
                   self.start2_button.config(state='disabled')
           else:
               self.running_2 = False
               self.start2_button.config(state='normal')
        
    def start_session(self):
        print("Начинаем новую сессию...")
        self.running = False
        self.running_1 = False
        self.running_2 = False
        self.session_number += 1
        self.current_session_value_label.config(text=self.session_number)
        for key in self.timer_activity:
            self.timer_activity[key] = 0
        self.time_1_label.config(text="00:00:00")
        self.time_2_label.config(text="00:00:00")
        self.start_current_session_sec = time.time()
        self.start_current_session = time.strftime("%Y-%m-%d %H:%M:%S",
                                                   time.localtime(self.start_current_session_sec))
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
        self.duration_current_session = time.strftime("%H:%M:%S",
                                                      time.gmtime(self.duration_current_session_sec))
        
        self.all_subsessions_by_session = self.db.get_subsessions_by_session(self.session_number)
        self.duration_total_act = {key: 0 for key in range(1, self.number_of_activities + 1)}
        self.duration_total_act_sec = {key: 0 for key in range(1, self.number_of_activities + 1)}
        for subsession in self.all_subsessions_by_session:
            hours, minutes, seconds = map(int, subsession['subs_duration'].split(':'))
            self.duration_total_act_sec[subsession['activity']] += 3600 * hours + 60 * minutes + seconds
        duration_total_acts_all_sec = 0
        for key in self.duration_total_act:
            self.duration_total_act[key] = time.strftime("%H:%M:%S",
                                                 time.gmtime(self.duration_total_act_sec[key]))
            duration_total_acts_all_sec += self.duration_total_act_sec[key]
        duration_total_acts_all = time.strftime("%H:%M:%S",
                                                 time.gmtime(duration_total_acts_all_sec))
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
            self.start_sess_datetime_label.config(text=self.duration_current_session)
        else:
            self.start_session()
            self.is_in_session = True
            self.start_sess_datetime_label.config(text=self.start_current_session)
        self.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[False])
        self.start1_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        self.start2_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        self.stop_button.config(state=BUTTON_PARAM_STATE_DICT[self.is_in_session])
        self.startterminate_session_button.config(text=BUTTON_SESSIONS_DICT[self.is_in_session])
        self.start_text_label.config(text=START_TEXT_LABEL_DICT[self.is_in_session])
        self.save_current_to_file()
        
    def retroactively_termination(self):
        # создаём диалоговое окно
        retroactively_termination_dialog = tk.Toplevel(self.root)
        
        # указываем, что наше диалоговое окно -- временное по отношению к родительскому окну
        # в т.ч. это убирает кнопки Свернуть/Развернуть, оставляя только крестик в углу
        retroactively_termination_dialog.transient(self.root)
        
        retroactively_termination_dialog.grab_set()   # блокируем кнопки родительского окна
        
        # задаём размеры окна
        width = 450
        height = 140
        
        # Получаем размеры основного окна - нужно для центрирования нашего окна
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - width // 2
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - height // 2
        
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
Эта функция вызывает саму себя и работает до тех пор, пока есть self.running
        """
        if not self.running: return
        #   Эти вещи нужны для замера и показа инфы, но для работы алгоритма оказались не нужны
        #   Хотя до этого думалось, что они нужны
        #   А потом математически я преобразовал выражение -- сократились! однако!
        #   По сути нужны только self.start_timer_time и self.timer_until_the_nearest_stop
        # start_update_time = time.perf_counter()  # начало замера
        # exact_elapsed_time = start_update_time - self.start_timer_time
        # delta = exact_elapsed_time - self.timer_until_the_nearest_stop - 1
        # print(exact_elapsed_time, delta)
        if self.working_timer == 1:
            self.timer_activity[self.activity_1] += 1
        else:
            self.timer_activity[self.activity_2] += 1 
        if self.running_1:
            self.time_1_label.config(text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_1])))
        if self.running_2:
            self.time_2_label.config(text=time.strftime("%H:%M:%S", time.gmtime(self.timer_activity[self.activity_2])))
        self.timer_until_the_nearest_stop += 1           
        self.root.after(
            int(1000*(1 + self.start_timer_time + self.timer_until_the_nearest_stop - time.perf_counter())),
            self.update_time
        )

    def update_time_starting(self):
        """
Стартовая точка вхождения в поток таймера.
Задаёт стартовые переменные и инициирует update_time, которая потом сама себя вызывает
        """
        self.start_timer_time = time.perf_counter()
        self.timer_until_the_nearest_stop = 0
        self.root.after(
            int(1000*(1 + self.start_timer_time + self.timer_until_the_nearest_stop - time.perf_counter())),
            self.update_time
        )

    def start_timer_1_hotkey(self, event):
        return self.start_timer_1()

    @time_decorator
    def start_timer_1(self):
        print("В начале функции start_timer_1, поток", threading.get_ident())
        if self.running and self.running_1:
            return
        self.running_1 = True
        self.running_2 = False
        self.working_timer = 1
        self.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[False])
        if not self.running:
            self.running = True
            self.on_select_combo_2(0)
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
        self.combobox_1.config(state='disabled')
        self.combobox_2.config(state='readonly')
        self.time_1_label.config(bg='green')
        self.time_2_label.config(bg=self.DEFAULT_WIN_COLOR)
        
    def start_timer_2_hotkey(self, event):
        return self.start_timer_2()

    @time_decorator
    def start_timer_2(self):
        print("В начале функции start_timer_2, поток", threading.get_ident())
        if self.running and self.running_2:
            return
        self.running_1 = False
        self.running_2 = True
        self.working_timer = 2
        self.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[False])
        if not self.running:
            self.running = True
            self.on_select_combo_1(0)
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
        self.combobox_1.config(state='readonly')
        self.combobox_2.config(state='disabled')
        self.time_1_label.config(bg=self.DEFAULT_WIN_COLOR)
        self.time_2_label.config(bg='green')            

    def stop_timers_hotkey(self, event):
        return self.stop_timers()
    
    @time_decorator
    def stop_timers(self):
        print("В начале функции stop_timers, поток", threading.get_ident())
        if not self.running:
            return
        self.running = False
        self.running_1 = False
        self.running_2 = False
        
        self.retroactively_termination_button.config(state=BUTTON_PARAM_STATE_DICT[True])
        self.combobox_1.config(state='readonly')
        self.combobox_2.config(state='readonly')
        self.start1_button.config(state='normal')
        self.start2_button.config(state='normal')
        self.time_1_label.config(bg=self.DEFAULT_WIN_COLOR)
        self.time_2_label.config(bg=self.DEFAULT_WIN_COLOR)
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
    root = tk.Tk()
    app = TrackerApp(root)
    root.mainloop()
