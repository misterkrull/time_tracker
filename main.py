import tkinter as tk
from gui.gui_layer import GuiLayer
from application_logic import ApplicationLogic


def main():
    app = ApplicationLogic()
    root = tk.Tk()
    GuiLayer(root, app)
    root.mainloop()


if __name__ == "__main__":
    main()
