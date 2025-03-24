TIMER_FRAME_COUNT = 3

# для 3 таймеров (и для прода) нужно 678, для пяти таймеров хорошо 1070
MAIN_WINDOW_X = 678
MAIN_WINDOW_Y = 250

BACKGROUND_COLOR = "SystemButtonFace"  # дефолтный виндовый цвет окон, типа серый такой

TK_BUTTON_STATES = {True: "normal", False: "disabled"}
TK_COMBOBOX_STATE = {True: "readonly", False: "disabled"}
TK_IS_GREEN_COLORED = {True: "green", False: BACKGROUND_COLOR}

SESSION_BUTTON_DICT = {True: "Завершить сессию", False: "Новая сессия"}
SESSION_LABEL_DICT = {True: "Началась: ", False: "Длилась: "}
