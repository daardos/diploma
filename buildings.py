import tkinter as tk
from database import get_buildings

class BaseView(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Моя база (вид сверху)")
        self.geometry("400x400")
        self.canvas = tk.Canvas(self, bg="darkgreen")
        self.canvas.pack(fill="both", expand=True)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        buildings = get_buildings()
        # Группировка по типам, автоматическое размещение на сетке
        placed = {}
        for name, x, y in buildings:
            placed[(x,y)] = name
        # Рисуем сетку 5x5
        for x in range(5):
            for y in range(5):
                color = "lightgray" if (x,y) not in placed else self.color_for(name)
                x1, y1 = x*80, y*80
                x2, y2 = x1+75, y1+75
                self.canvas.create_rectangle(x1,y1,x2,y2, fill=color, outline="black")
                if (x,y) in placed:
                    self.canvas.create_text(x1+37, y1+37, text=placed[(x,y)][:4], font=("Arial",8))

    def color_for(self, name):
        if "Стена" in name: return "gray"
        if "Дверь" in name: return "brown"
        if "Верстак" in name: return "orange"
        if "Кровать" in name: return "red"
        if "Печь" in name: return "darkred"
        return "white"