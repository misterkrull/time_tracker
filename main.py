import json
import tkinter as tk
from pathlib import Path

from application_logic import ApplicationLogic
from db_manager import DB
from gui.gui_layer import GuiLayer


SETTINGS_FILENAME = "settings.json"


def main():
    settings = {}
    settings_filepath = Path(__file__).absolute().parent / SETTINGS_FILENAME
    if settings_filepath.exists():
        with open(settings_filepath, 'r') as f:
            settings = json.load(f)

    db = DB(settings)
    app = ApplicationLogic(db)
    root = tk.Tk()

    GuiLayer(root, app, settings)
    root.mainloop()


if __name__ == "__main__":
    main()
