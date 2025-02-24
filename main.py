import tkinter as tk
from gui_layer import GuiLayer
from time_tracker import ApplicationLogic


def main():
    app = ApplicationLogic()
    root = tk.Tk()
    GuiLayer(root, app)
    root.mainloop()


if __name__ == "__main__":
    main()
