import random
import json
from database import (player, save_player, add_item, remove_item, item_qty,
                      is_bp_learned, get_buildings, get_learned_bps)

# Загружаем JSON с предметами, чертежами, крафтами
with open("game_data.json", "r", encoding="utf-8") as f:
    GAME_DATA = json.load(f)

# ---------- ЖИВОТНЫЕ ----------
ANIMALS = [
    {"name": "Волк", "hp": 40, "max_hp": 40, "dmg": (5, 15), "loot": {"Сырое мясо": 2, "Кожа": 3, "Кости": 5}},
    {"name": "Кабан", "hp": 60, "max_hp": 60, "dmg": (8, 18), "loot": {"Сырое мясо": 4, "Кожа": 5, "Кости": 8}},
    {"name": "Медведь", "hp": 80, "max_hp": 80, "dmg": (10, 25), "loot": {"Сырое мясо": 6, "Кожа": 10, "Кости": 12}},
]

# ---------- ДЕНЬ/НОЧЬ ----------
def update_day_night():
    player["day"] += 0.01
    if player["day"] >= 1:
        player["day"] = 0
        # Переключаем время суток
        player["time_of_day"] = "Ночь" if player["time_of_day"] == "День" else "День"
    save_player(player)

# ---------- ГОЛОД/ЖАЖДА ----------
def update_survival():
    player["hunger"] = max(0, player["hunger"] - 0.3)
    player["thirst"] = max(0, player["thirst"] - 0.4)
    if player["hunger"] == 0:
        player["hp"] = max(1, player["hp"] - 2)
    if player["thirst"] == 0:
        player["hp"] = max(1, player["hp"] - 3)
    save_player(player)

# ---------- СЛУЧАЙНЫЕ СОБЫТИЯ ПРИ ПЕРЕМЕЩЕНИИ ----------
def random_event(location):
    """Возвращает название события или None"""
    if location == "Лес" and random.random() < 0.3:
        return "Волк"
    elif location == "Горы" and random.random() < 0.4:
        return "Медведь"
    elif location == "РТ (Рад. Город)" and random.random() < 0.5:
        return "Радиационный шторм"
    # Шанс на рейдера в любой локации, кроме Пляжа
    if location != "Пляж" and random.random() < 0.15:
        return "Рейдер"
    return None

# ---------- РЕЙД НА БАЗУ ----------
def raid_base():
    buildings = get_buildings()
    # Проверяем наличие стен или дверей
    has_defense = any("Стена" in b[0] or "Дверь" in b[0] for b in buildings)
    if not has_defense:
        # Могут украсть случайный ресурс
        possible = ["Скрап", "Металлическая руда", "Дерево"]
        stolen_item = random.choice(possible)
        qty = min(10, item_qty(stolen_item))
        if qty > 0:
            remove_item(stolen_item, qty)
            return f"Рейдеры прорвались в незащищённую базу и украли {stolen_item} x{qty}!"
        else:
            return "Рейдеры попытались ограбить базу, но украли только пыль."
    else:
        return "Рейдеры атаковали, но ваша база хорошо укреплена — вы отбились!"

# ---------- КРАФТ ----------
def get_workbench_level_required(item_name):
    """Возвращает минимальный уровень верстака (1, 2, 3 или 0)"""
    wb1 = ["Арбалет", "Револьвер", "Пистолет", "Дробовик", "Винтовка", "AK-47",
           "Снайперская винтовка", "Ракетница", "Граната", "Патроны для пистолета",
           "Патроны 5.56", "Патроны для дробовика", "Ракета",
           "Металлический шлем", "Металлический нагрудник", "Тактический жилет",
           "Каменный фундамент", "Каменная стена", "Каменный потолок",
           "Металлическая стена", "Металлическая дверь", "Двойная дверь",
           "Люк", "Окно с решеткой", "Шестерня", "Пружина", "Электронная плата",
           "Труба", "Лист металла", "Винт", "Генератор", "Лампа", "Выключатель",
           "Турель", "Верстак 2 уровня", "Исследовательский стол"]
    if item_name in wb1:
        return 1
    if item_name == "Верстак 3 уровня":
        return 2
    return 0

def can_craft(item_name):
    """Проверяет, можно ли скрафтить предмет. Возвращает (True/False, причина)"""
    # Ищем рецепт
    recipe = None
    for craft in GAME_DATA["crafts"]:
        if craft["result_item"] == item_name:
            recipe = craft
            break
    if not recipe:
        return False, "Рецепт не найден"
    # Проверяем чертёж
    if not is_bp_learned(item_name, GAME_DATA["blueprints"]):
        return False, "Чертёж не изучен"
    # Проверяем верстак
    wb_lvl = get_workbench_level_required(item_name)
    if wb_lvl > 0:
        wb_name = f"Верстак {wb_lvl} уровня"
        if item_qty(wb_name) < 1:
            return False, f"Требуется {wb_name} в инвентаре"
    # Проверяем ингредиенты
    for ing in recipe["ingredients"]:
        if item_qty(ing["name"]) < ing["amount"]:
            return False, f"Недостаточно {ing['name']} (нужно {ing['amount']})"
    return True, ""

def craft_item(item_name):
    """Скрафтить предмет: забирает ингредиенты, даёт результат"""
    recipe = None
    for craft in GAME_DATA["crafts"]:
        if craft["result_item"] == item_name:
            recipe = craft
            break
    if not recipe:
        return
    for ing in recipe["ingredients"]:
        remove_item(ing["name"], ing["amount"])
    add_item(item_name, recipe["quantity"])

# ---------- БОЕВОЙ УРОН ИГРОКА ----------
def player_damage():
    """Вычисляет урон игрока с учётом самого мощного оружия в инвентаре"""
    base = random.randint(5, 10)
    weapons = {
        "Топор": 10, "Кирка": 5, "Лук": 15, "Арбалет": 20, "Револьвер": 25,
        "Пистолет": 30, "Дробовик": 35, "Винтовка": 40, "AK-47": 50,
        "Снайперская винтовка": 60, "Ракетница": 100
    }
    bonus = 0
    for weapon, dmg in weapons.items():
        if item_qty(weapon) > 0:
            bonus = max(bonus, dmg)
    return base + bonus