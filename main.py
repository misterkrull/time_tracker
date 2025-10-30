import tkinter as tk
from tkinter import messagebox

from application_logic import ApplicationLogic
from db_manager import DB
from exceptions import TimeTrackerError
from gui.gui_layer import GuiLayer
from settings_loader import load_settings


def main():
    settings = load_settings()  # путь в файлу настроек лежит в filenames.py

    db = DB(settings)
    app = ApplicationLogic(db)
    root = tk.Tk()

    GuiLayer(root, app, settings)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except TimeTrackerError as err:
        messagebox.showerror("Ошибка", str(err))
