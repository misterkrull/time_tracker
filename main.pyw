import traceback
from tkinter import messagebox

from exceptions import TimeTrackerError
from main import main


if __name__ == "__main__":
    try:
        main()
    except TimeTrackerError as err:
        messagebox.showerror("Ошибка", str(err))
    except:  # noqa: E722
        messagebox.showerror("Ошибка", traceback.format_exc())
        