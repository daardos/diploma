import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import time
from database import (player, save_player, add_item, remove_item, get_inventory,
                      item_qty, learn_bp, get_learned_bps, is_bp_learned,
                      get_buildings, add_building)
from game_logic import (update_day_night, update_survival, random_event,
                        raid_base, GAME_DATA, ANIMALS, can_craft, craft_item,
                        get_workbench_level_required, player_damage)
from buildings import BaseView

class GameUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RUST: Survival Edition")
        self.root.geometry("650x750")
        self.root.resizable(False, False)

        # Верхний HUD
        self.lbl_status = tk.Label(root, text="", font=("Arial", 10, "bold"),
                                   relief="groove", bd=2, padx=10, pady=5)
        self.lbl_status.pack(side=tk.TOP, fill=tk.X)

        # Консоль
        self.console = scrolledtext.ScrolledText(root, height=8, state="disabled",
                                                 bg="black", fg="lime", font=("Consolas", 10))
        self.console.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=5, pady=5)

        # Центральный контейнер для переключения экранов
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Фреймы
        self.frame_menu = tk.Frame(self.main_frame)
        self.frame_combat = tk.Frame(self.main_frame)

        # Текущий враг
        self.current_enemy = None

        # Построить меню
        self.build_menu()
        self.show_menu()

        # Запуск фоновых обновлений
        self.update_survival_loop()
        self.update_day_loop()

        # Обновить HUD
        self.update_hud()

    def console_log(self, msg):
        """Вывод в консоль"""
        self.console.config(state="normal")
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def update_hud(self):
        """Обновить строку статуса"""
        day_emoji = "☀️" if player["time_of_day"] == "День" else "🌙"
        status = (f"👤 {player['name']} | ❤️ {player['hp']}/100 | 🍖 {int(player['hunger'])}% "
                  f"💧 {int(player['thirst'])}% | ⚙️ {player['scrap']} скрапа | "
                  f"{day_emoji} {player['time_of_day']} | 🗺️ {player['location']}")
        self.lbl_status.config(text=status)

    def show_menu(self):
        self.frame_combat.pack_forget()
        self.frame_menu.pack(fill=tk.BOTH, expand=True)

    def show_combat(self):
        self.frame_menu.pack_forget()
        self.frame_combat.pack(fill=tk.BOTH, expand=True)
        self.update_combat_hud()

    # ----------------------------------------------------------------
    # ГЛАВНОЕ МЕНЮ
    # ----------------------------------------------------------------
    def build_menu(self):
        # Кнопки
        buttons = [
            ("🔨 Искать компоненты (Лутать)", self.loot_action, "#556B2F"),
            ("🪓 Собрать ресурсы", self.collect_resources, "#8B4513"),
            ("🎒 Инвентарь", self.open_inventory, None),
            ("🔧 Крафт", self.open_craft, None),
            ("📜 Чертежи", self.open_blueprints, None),
            ("🏗️ Строительство", self.open_building, None),
            ("🗺️ Карта", self.open_map, None),
            ("⚔️ Охота", self.start_hunt, "#8B0000"),
            ("🏰 Моя база", self.show_base_view, None),
            ("🛡️ Проверить рейд", self.check_raid, "#B8860B"),
            ("❌ Выйти", self.root.quit, None)
        ]

        for text, cmd, color in buttons:
            btn = tk.Button(self.frame_menu, text=text, font=("Arial", 11),
                            command=cmd, bg=color if color else "SystemButtonFace",
                            fg="white" if color else "black")
            btn.pack(pady=4, fill=tk.X, padx=30)

        # Фрейм боя
        self.lbl_enemy = tk.Label(self.frame_combat, text="", font=("Arial", 12, "bold"))
        self.lbl_enemy.pack(pady=10)

        btn_attack = tk.Button(self.frame_combat, text="⚔️ Атаковать", command=self.player_attack,
                               bg="#8B0000", fg="white")
        btn_attack.pack(pady=5, fill=tk.X, padx=50)

        btn_heal = tk.Button(self.frame_combat, text="💉 Лечиться", command=self.player_heal,
                             bg="#228B22", fg="white")
        btn_heal.pack(pady=5, fill=tk.X, padx=50)

        btn_flee = tk.Button(self.frame_combat, text="🏃 Убежать", command=self.player_flee,
                             bg="#B8860B", fg="white")
        btn_flee.pack(pady=5, fill=tk.X, padx=50)

    def update_combat_hud(self):
        if self.current_enemy:
            self.lbl_enemy.config(text=f"{self.current_enemy['name']} | ❤️ {self.current_enemy['hp']}/{self.current_enemy['max_hp']}")
        else:
            self.lbl_enemy.config(text="")

    # ----------------------------------------------------------------
    # ФОНОВЫЕ ПРОЦЕССЫ
    # ----------------------------------------------------------------
    def update_survival_loop(self):
        """Каждые 3 секунды снижаем голод и жажду"""
        update_survival()
        if player["hp"] <= 0:
            self.handle_death()
        self.update_hud()
        self.root.after(3000, self.update_survival_loop)

    def update_day_loop(self):
        """Каждые 30 секунд сдвигаем время суток"""
        update_day_night()
        self.update_hud()
        self.root.after(30000, self.update_day_loop)

    def handle_death(self):
        """Смерть: возрождение с потерями"""
        # Проверяем, есть ли кровать в постройках
        buildings = get_buildings()
        has_bed = any("Кровать" in b[0] for b in buildings)
        if has_bed:
            player["hp"] = 100
            player["scrap"] = int(player["scrap"] * 0.8)  # теряем 20%
            player["location"] = "База"
            msg = "💀 Вы погибли, но ваша кровать спасла вас! Возрождение на базе. Потеряно 20% скрапа."
        else:
            player["hp"] = 100
            player["scrap"] = int(player["scrap"] * 0.5)
            player["location"] = "Пляж"
            msg = "💀 Вы погибли! Возрождение на Пляже. Потеряно 50% скрапа."
        save_player(player)
        self.console_log(msg)
        self.show_menu()

    # ----------------------------------------------------------------
    # ДЕЙСТВИЯ
    # ----------------------------------------------------------------
    def loot_action(self):
        loc = player["location"]
        if loc == "Пляж":
            scrap = random.randint(5, 15)
            dmg = 0
        elif loc == "Лес":
            scrap = random.randint(15, 30)
            dmg = 0
        elif loc == "Горы":
            scrap = random.randint(25, 50)
            dmg = 0
        elif loc == "РТ (Рад. Город)":
            scrap = random.randint(50, 120)
            dmg = random.randint(5, 15)
        else:
            scrap, dmg = 0, 0

        player["scrap"] += scrap
        player["hp"] -= dmg
        save_player(player)

        msg = f"🔨 Найдено {scrap} скрапа"
        if dmg > 0:
            msg += f" (получено {dmg} урона радиацией)"
        self.console_log(msg)

        if player["hp"] <= 0:
            self.handle_death()
        self.update_hud()

    def collect_resources(self):
        loc = player["location"]
        resources = {}
        if loc == "Пляж":
            resources = {"Дерево": random.randint(10, 30), "Камень": random.randint(5, 15)}
        elif loc == "Лес":
            resources = {"Дерево": random.randint(40, 80), "Ткань": random.randint(5, 10)}
        elif loc == "Горы":
            resources = {"Камень": random.randint(30, 60), "Металлическая руда": random.randint(5, 15)}
        elif loc == "РТ (Рад. Город)":
            resources = {"Металлическая руда": random.randint(10, 30), "Серная руда": random.randint(5, 15)}
            dmg = random.randint(3, 10)
            player["hp"] -= dmg
            save_player(player)
            if player["hp"] <= 0:
                self.handle_death()
                return
            self.console_log(f"☢️ Облучение: -{dmg} HP")

        # Бонус инструментов
        if item_qty("Топор") > 0 and "Дерево" in resources:
            resources["Дерево"] = int(resources["Дерево"] * 1.5)
        if item_qty("Кирка") > 0:
            for res in ["Камень", "Металлическая руда", "Серная руда"]:
                if res in resources:
                    resources[res] = int(resources[res] * 1.5)

        for res, qty in resources.items():
            add_item(res, qty)

        self.console_log("🪓 Собрано: " + ", ".join(f"{k} +{v}" for k, v in resources.items()))
        self.update_hud()

    # ----------------------------------------------------------------
    # ОХОТА И БОЙ
    # ----------------------------------------------------------------
    def start_hunt(self):
        if self.current_enemy:
            self.console_log("Вы уже сражаетесь!")
            return
        animal = random.choice(ANIMALS)
        self.current_enemy = {
            "name": animal["name"],
            "hp": animal["hp"],
            "max_hp": animal["hp"],
            "dmg": animal["dmg"],
            "loot": animal["loot"]
        }
        self.console_log(f"⚔️ Вы встретили {self.current_enemy['name']} (❤️ {self.current_enemy['hp']})!")
        self.show_combat()

    def player_attack(self):
        if not self.current_enemy:
            return
        dmg = player_damage()
        self.current_enemy["hp"] -= dmg
        self.console_log(f"Вы атакуете {self.current_enemy['name']} на {dmg} урона.")
        if self.current_enemy["hp"] <= 0:
            self.console_log(f"💀 Вы убили {self.current_enemy['name']}!")
            for loot_name, qty in self.current_enemy["loot"].items():
                add_item(loot_name, qty)
                self.console_log(f"   + {loot_name} x{qty}")
            self.current_enemy = None
            self.show_menu()
            self.update_hud()
            return
        self.enemy_turn()

    def enemy_turn(self):
        if not self.current_enemy:
            return
        dmg = random.randint(*self.current_enemy["dmg"])
        player["hp"] -= dmg
        save_player(player)
        self.console_log(f"{self.current_enemy['name']} атакует вас на {dmg} урона.")
        if player["hp"] <= 0:
            self.handle_death()
            self.current_enemy = None
            self.show_menu()
            return
        self.update_combat_hud()
        self.update_hud()

    def player_heal(self):
        if item_qty("Медицинский шприц") > 0:
            remove_item("Медицинский шприц", 1)
            heal = 30
        elif item_qty("Большая аптечка") > 0:
            remove_item("Большая аптечка", 1)
            heal = 50
        else:
            self.console_log("❌ Нет аптечек!")
            return
        player["hp"] = min(100, player["hp"] + heal)
        save_player(player)
        self.console_log(f"💉 Вы восстановили {heal} HP.")
        self.enemy_turn()
        self.update_hud()
        self.update_combat_hud()

    def player_flee(self):
        if random.random() < 0.5:
            self.console_log("🏃 Вы сбежали!")
            self.current_enemy = None
            self.show_menu()
        else:
            self.console_log("❌ Не удалось убежать!")
            self.enemy_turn()
            self.update_combat_hud()
        self.update_hud()

    # ----------------------------------------------------------------
    # СОБЫТИЯ ПРИ ПЕРЕМЕЩЕНИИ (вызывается из карты)
    # ----------------------------------------------------------------
    def travel_to(self, location):
        player["location"] = location
        save_player(player)
        self.console_log(f"🗺️ Вы переместились на {location}")

        event = random_event(location)
        if event:
            if event == "Радиационный шторм":
                dmg = random.randint(10, 20)
                player["hp"] -= dmg
                save_player(player)
                self.console_log(f"☢️ Радиационный шторм! Вы получили {dmg} урона.")
                if player["hp"] <= 0:
                    self.handle_death()
            elif event in ["Волк", "Медведь"]:
                animal_data = next(a for a in ANIMALS if a["name"] == event)
                self.current_enemy = {
                    "name": animal_data["name"],
                    "hp": animal_data["hp"],
                    "max_hp": animal_data["hp"],
                    "dmg": animal_data["dmg"],
                    "loot": animal_data["loot"]
                }
                self.console_log(f"⚔️ На вас напал {event}!")
                self.show_combat()
                return
            elif event == "Рейдер":
                raider = {"name": "Рейдер", "hp": 50, "max_hp": 50, "dmg": (10, 20),
                          "loot": {"Скрап": 30}}
                self.current_enemy = raider
                self.console_log("🔫 Вас атакует рейдер!")
                self.show_combat()
                return
        self.update_hud()

    # ----------------------------------------------------------------
    # ОКНА (инвентарь, крафт, чертежи, карта, строительство, база)
    # ----------------------------------------------------------------
    def open_inventory(self):
        win = tk.Toplevel(self.root)
        win.title("Инвентарь")
        win.geometry("300x400")
        listbox = tk.Listbox(win, font=("Arial", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for name, qty in get_inventory():
            listbox.insert(tk.END, f"{name} (x{qty})")
        tk.Button(win, text="Закрыть", command=win.destroy).pack(pady=5)

    def open_craft(self):
        win = tk.Toplevel(self.root)
        win.title("Крафт")
        win.geometry("400x500")
        listbox = tk.Listbox(win, font=("Arial", 9))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def refresh_list():
            listbox.delete(0, tk.END)
            for craft in GAME_DATA["crafts"]:
                item = craft["result_item"]
                ok, reason = can_craft(item)
                status = "✅" if ok else f"❌ {reason}"
                listbox.insert(tk.END, f"{item} – {status}")

        def do_craft():
            sel = listbox.curselection()
            if not sel:
                return
            item = GAME_DATA["crafts"][sel[0]]["result_item"]
            ok, reason = can_craft(item)
            if not ok:
                self.console_log(f"Ошибка крафта: {reason}")
                return
            craft_item(item)
            self.console_log(f"🔧 Скрафчено: {item}")
            refresh_list()
            self.update_hud()

        refresh_list()
        tk.Button(win, text="⚒️ Скрафтить", command=do_craft, bg="#8B0000", fg="white").pack(pady=5)
        tk.Button(win, text="Закрыть", command=win.destroy).pack(pady=5)

    def open_blueprints(self):
        win = tk.Toplevel(self.root)
        win.title("Чертежи")
        win.geometry("400x500")
        listbox = tk.Listbox(win, font=("Arial", 9))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for bp in GAME_DATA["blueprints"]:
                name = bp["item_name"]
                if is_bp_learned(name, GAME_DATA["blueprints"]):
                    status = "✅ изучено"
                else:
                    status = f"❌ ({bp['scrap_to_learn']} скрапа)"
                listbox.insert(tk.END, f"{name} – {status}")

        def learn():
            sel = listbox.curselection()
            if not sel:
                return
            bp = GAME_DATA["blueprints"][sel[0]]
            name = bp["item_name"]
            if is_bp_learned(name, GAME_DATA["blueprints"]):
                self.console_log("Уже изучено")
                return
            if player["scrap"] < bp["scrap_to_learn"]:
                self.console_log("Недостаточно скрапа")
                return
            player["scrap"] -= bp["scrap_to_learn"]
            save_player(player)
            learn_bp(name)
            self.console_log(f"📜 Изучен: {name}")
            refresh()
            self.update_hud()

        refresh()
        tk.Button(win, text="🔬 Изучить", command=learn, bg="#8B0000", fg="white").pack(pady=5)
        tk.Button(win, text="Закрыть", command=win.destroy).pack(pady=5)

    def open_map(self):
        win = tk.Toplevel(self.root)
        win.title("Карта")
        win.geometry("300x280")
        tk.Label(win, text="🗺️ Выберите локацию:", font=("Arial", 12, "bold")).pack(pady=10)
        for loc, desc in [("Пляж", "🏖️ Безопасно, мало лута"),
                          ("Лес", "🌲 Средне лута"),
                          ("Горы", "🏔️ Много лута"),
                          ("РТ (Рад. Город)", "☢️ Огромный лут, радиация")]:
            tk.Button(win, text=desc, command=lambda l=loc: [win.destroy(), self.travel_to(l)]).pack(
                fill=tk.X, padx=20, pady=3)

    def open_building(self):
        win = tk.Toplevel(self.root)
        win.title("Строительство")
        win.geometry("400x500")
        listbox = tk.Listbox(win, font=("Arial", 9))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        items = ["Верстак 1 уровня", "Верстак 2 уровня", "Верстак 3 уровня",
                 "Деревянный фундамент", "Деревянная стена", "Деревянный потолок",
                 "Каменный фундамент", "Каменная стена", "Каменный потолок",
                 "Металлическая стена", "Металлическая дверь", "Двойная дверь",
                 "Люк", "Окно с решеткой", "Кровать", "Печь", "Ящик"]
        built = [b[0] for b in get_buildings()]

        def refresh():
            listbox.delete(0, tk.END)
            for item in items:
                if item in built:
                    status = "✅ Построено"
                else:
                    qty = item_qty(item)
                    status = f"📦 {qty} шт." if qty > 0 else "❌ Нет"
                listbox.insert(tk.END, f"{item} – {status}")

        def build():
            sel = listbox.curselection()
            if not sel:
                return
            name = items[sel[0]]
            if name in built:
                self.console_log("Уже построено")
                return
            if remove_item(name, 1):
                # Автоматическое размещение на свободную клетку
                all_builds = get_buildings()
                occupied = [(b[1], b[2]) for b in all_builds]
                for x in range(5):
                    for y in range(5):
                        if (x, y) not in occupied:
                            add_building(name, x, y)
                            self.console_log(f"🏗️ Построено: {name} на клетке ({x},{y})")
                            refresh()
                            return
                self.console_log("Нет свободного места на базе!")
            else:
                self.console_log("Недостаточно предметов в инвентаре")

        refresh()
        tk.Button(win, text="🔨 Построить", command=build, bg="#8B4513", fg="white").pack(pady=5)
        tk.Button(win, text="Закрыть", command=win.destroy).pack(pady=5)

    def show_base_view(self):
        BaseView(self.root)

    def check_raid(self):
        msg = raid_base()
        self.console_log("🛡️ Рейд: " + msg)