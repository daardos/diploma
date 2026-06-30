import tkinter as tk
from database import init_db, load_player, player
from ui import GameUI

init_db()
window = tk.Tk()
app = GameUI(window)
window.mainloop()