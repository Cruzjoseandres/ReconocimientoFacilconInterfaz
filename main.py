import tkinter as tk
from logic import FaceAppLogic
from ui import FaceAppUI


if __name__ == "__main__":
    root = tk.Tk()
    logic = FaceAppLogic()
    app = FaceAppUI(root, logic)
    root.mainloop()