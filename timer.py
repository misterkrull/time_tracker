import tkinter as tk
from tkinter import ttk

from common_functions import sec_to_time, time_decorator
from time_counter import TimeCounter
from subsession import Subsession

TK_BUTTON_STATES = {True: "normal", False: "disabled"}


class TimeTrackerTimer:
    def __init__(
            self,
            id: int,
            activity_number: int,
            gui_layer, 
            main_frame: tk.Frame,
            timer_activity_names: dict[int, str]
    ):
        self.id = id
        self.activity_number = activity_number
        self.is_running: bool = False

        self._gui_layer = gui_layer
        self._timer_activity_names = timer_activity_names  # может заполнять этот список уже здесь?
        self._gui_init_combobox_value: tk.StringVar | None = None
        self.gui_label: tk.Label | None = None
        self.gui_combobox: ttk.Combobox | None = None
        self.gui_start_button: tk.Button | None = None

        self._init_gui_(main_frame)

    def _init_gui_(self, main_frame: tk.Frame) -> None:
        timer_frame = tk.Frame(main_frame)
        timer_frame.pack(side=tk.LEFT, padx=10)

        # Лейбл
        self.gui_label = tk.Label(
            timer_frame,
            text=sec_to_time(
                self._gui_layer.app.durations_of_activities_in_current_session[self.activity_number]
            ),
            font=("Helvetica", 36),
        )
        self.gui_label.pack()

        # Комбобокс
        self._gui_init_combobox_value = (
            tk.StringVar()
        )  # нужен для работы с выбранным значением комбобокса
        self._gui_init_combobox_value.set(self._timer_activity_names[self.activity_number])

        self.gui_combobox = ttk.Combobox(
            timer_frame,
            textvariable=self._gui_init_combobox_value,
            values=list(self._timer_activity_names.values()),
            state="readonly",
        )
        self.gui_combobox.pack(pady=5)
        self.gui_combobox.bind("<<ComboboxSelected>>", self._select_activity)

        # Кнопка "Старт <timer_number>"
        self.gui_start_button = tk.Button(
            timer_frame,
            text=f"Старт {self.id}",
            command=self._start_timer,
            font=("Helvetica", 14),
            width=10,
            height=1,
            state=TK_BUTTON_STATES[self._gui_layer.app.is_in_session],
        )
        self.gui_start_button.pack(pady=5)

    # TODO вернуть тут аннотацию
    # def _select_activity(self, _: tk.Event[ttk.Combobox]):
    def _select_activity(self, _):  
        # Combobox считает с 0, а мы с 1
        self.activity_number = self.gui_combobox.current() + 1

        self.gui_label.config(
            text=sec_to_time(self._gui_layer.app.durations_of_activities_in_current_session[self.activity_number])
        )

        for other_timer in self._gui_layer.timer_list:
            if other_timer.id == self.id:
                continue

            if other_timer.is_running:
                is_same_activity = self.activity_number == other_timer.activity_number
                self.is_running = is_same_activity
                self.gui_start_button.config(state=TK_BUTTON_STATES[not is_same_activity])
                return

    @time_decorator
    def _start_timer(self) -> None:
        """
        Запускается при нажатии на кнопку "Старт <timer.id>"
        """
        if self.is_running:
            return

        if all(
            not timer.is_running for timer in self._gui_layer.timer_list
        ):  # старт "с нуля", т.е. все таймеры стояли
            self._starting_new_timer()
        else:  # переключение таймера, т.е. какой-то таймер работал
            self._switching_timer()

    def _starting_new_timer(self) -> None:
        for timer in self._gui_layer.timer_list:
            if timer.activity_number == self.activity_number:
                timer.is_running = True
                timer.gui_start_button.config(state=TK_BUTTON_STATES[False])
                # кстати, от засеривания кнопок я возможно уйду: так-то прикольно было бы перекинуть
                # работающий таймер с одной позиции на другую
                # кстати, можно вообще засеривать только текущую кнопку -- т.е. результат будет на 100% 
                #   противоположен тому, что было когда-то раньше xDDDD

        self.gui_combobox.config(state="disable")
        self.gui_label.config(bg="green")
        self._gui_layer.retroactively_terminate_session_button.config(state=TK_BUTTON_STATES[False])

        self._gui_layer.time_counter = TimeCounter(self._gui_layer, self.activity_number)
        self._gui_layer.subsession = Subsession(self._gui_layer.time_counter, self._gui_layer.app)

    def _switching_timer(self) -> None:
        for timer in self._gui_layer.timer_list:
            if timer.activity_number == self.activity_number:
                timer.is_running = True
                timer.gui_start_button.config(state=TK_BUTTON_STATES[False])
                # кстати, от засеривания кнопок я возможно уйду: так-то прикольно было бы перекинуть
                # работающий таймер с одной позиции на другую
                # кстати, можно вообще засеривать только текущую кнопку -- т.е. результат будет на 100% 
                #   противоположен тому, что было когда-то раньше xDDDD

        # приходится вызывать это дело отдельно, чтобы не было промежуточной ситуации, 
        #   когда у всех таймеров все is_running равны False
            # TODO уже походу эта механика не актуальна, т.к. update_time() уже живёт по собственному флагу,
            #   а не проверяет всякий раз все из_раннинги у каждого таймера
        for timer in self._gui_layer.timer_list:
            if timer.activity_number != self.activity_number:
                timer.is_running = False
                timer.gui_start_button.config(state=TK_BUTTON_STATES[True])
                timer.gui_combobox.config(state="readonly")
                timer.gui_label.config(bg=self._gui_layer.DEFAULT_WIN_COLOR)

        self.gui_combobox.config(state="disable")
        self.gui_label.config(bg="green")

        self._gui_layer.time_counter.current_activity = self.activity_number

        # NOTE приходится сначала инициализировать новую субсессию, чтобы точное текущее время для неё застолбить,
        # делаем это сейчас, т.к. впереди у нас дооолгий запрос к БД (в self._gui_layer.subsession.ending()),
        # который должен выполняться от лица старой субсессии
        # только после выполнения этого запроса уже обновляем self._gui_layer.subsession
            # вообще говоря это костыль, а по уму нужно делать асинхронку или что-то в этом духе
            # TODO убрать этот костыль и сделать по уму
        new_subsession = Subsession(self._gui_layer.time_counter, self._gui_layer.app)
        self._gui_layer.subsession.ending()
        self._gui_layer.subsession = new_subsession
