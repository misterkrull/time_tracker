import tkinter as tk
import yaml
from pathlib import Path
from tkinter import messagebox

from application_logic import ApplicationLogic
from db_manager import DB
from exceptions import TimeTrackerError
from gui.gui_layer import GuiLayer


SETTINGS_FILENAME = "settings.yaml"


def main():
    settings = {}
    settings_filepath = Path(__file__).absolute().parent / SETTINGS_FILENAME
    if settings_filepath.exists():
        with open(settings_filepath, 'r') as f:
            settings = yaml.safe_load(f)

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
