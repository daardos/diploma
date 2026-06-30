import sqlite3

DB_NAME = "rust_game.db"
PLAYER_ID = 1

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY, name TEXT, hp INTEGER DEFAULT 100,
        scrap INTEGER DEFAULT 0, location TEXT DEFAULT 'Пляж',
        hunger INTEGER DEFAULT 100, thirst INTEGER DEFAULT 100,
        day REAL DEFAULT 0, time_of_day TEXT DEFAULT 'День')''')
    c.execute('''CREATE TABLE IF NOT EXISTS blueprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER,
        item_name TEXT, is_learned INTEGER DEFAULT 0,
        FOREIGN KEY(player_id) REFERENCES players(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER,
        item_name TEXT, quantity INTEGER,
        FOREIGN KEY(player_id) REFERENCES players(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS buildings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER,
        item_name TEXT, is_built INTEGER DEFAULT 1,
        pos_x INTEGER DEFAULT 0, pos_y INTEGER DEFAULT 0,
        FOREIGN KEY(player_id) REFERENCES players(id))''')
    conn.commit()
    conn.close()

def load_player():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE id=?", (PLAYER_ID,))
    row = c.fetchone()
    if row:
        player = {
            "id": row[0], "name": row[1], "hp": row[2], "scrap": row[3],
            "location": row[4], "hunger": row[5], "thirst": row[6],
            "day": row[7], "time_of_day": row[8]
        }
    else:
        player = {"id": PLAYER_ID, "name": "Facepuncher", "hp": 100, "scrap": 0,
                  "location": "Пляж", "hunger": 100, "thirst": 100,
                  "day": 0, "time_of_day": "День"}
        c.execute("INSERT INTO players VALUES (?,?,?,?,?,?,?,?,?)",
                  (PLAYER_ID, player["name"], player["hp"], player["scrap"],
                   player["location"], player["hunger"], player["thirst"],
                   player["day"], player["time_of_day"]))
        conn.commit()
    conn.close()
    return player

def save_player(p):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE players SET hp=?, scrap=?, location=?, hunger=?, thirst=?, day=?, time_of_day=? WHERE id=?",
              (p["hp"], p["scrap"], p["location"], p["hunger"], p["thirst"],
               p["day"], p["time_of_day"], p["id"]))
    conn.commit()
    conn.close()

def add_item(item_name, qty):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, quantity FROM inventory WHERE player_id=? AND item_name=?",
              (PLAYER_ID, item_name))
    row = c.fetchone()
    if row:
        c.execute("UPDATE inventory SET quantity=? WHERE id=?", (row[1]+qty, row[0]))
    else:
        c.execute("INSERT INTO inventory (player_id, item_name, quantity) VALUES (?,?,?)",
                  (PLAYER_ID, item_name, qty))
    conn.commit()
    conn.close()

def remove_item(item_name, qty):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, quantity FROM inventory WHERE player_id=? AND item_name=?",
              (PLAYER_ID, item_name))
    row = c.fetchone()
    if not row or row[1] < qty:
        conn.close()
        return False
    new_qty = row[1] - qty
    if new_qty == 0:
        c.execute("DELETE FROM inventory WHERE id=?", (row[0],))
    else:
        c.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, row[0]))
    conn.commit()
    conn.close()
    return True

def get_inventory():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT item_name, quantity FROM inventory WHERE player_id=? ORDER BY item_name",
              (PLAYER_ID,))
    items = c.fetchall()
    conn.close()
    return items

def item_qty(item_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT quantity FROM inventory WHERE player_id=? AND item_name=?",
              (PLAYER_ID, item_name))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def learn_bp(item_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM blueprints WHERE player_id=? AND item_name=?", (PLAYER_ID, item_name))
    if c.fetchone():
        c.execute("UPDATE blueprints SET is_learned=1 WHERE player_id=? AND item_name=?", (PLAYER_ID, item_name))
    else:
        c.execute("INSERT INTO blueprints (player_id, item_name, is_learned) VALUES (?,?,1)",
                  (PLAYER_ID, item_name))
    conn.commit()
    conn.close()

def get_learned_bps():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT item_name FROM blueprints WHERE player_id=? AND is_learned=1", (PLAYER_ID,))
    items = [r[0] for r in c.fetchall()]
    conn.close()
    return items

def is_bp_learned(item_name, default_learned_list):
    if item_name in get_learned_bps():
        return True
    for bp in default_learned_list:
        if bp["item_name"] == item_name and bp["default_learned"] == 1:
            return True
    return False

def add_building(item_name, x, y):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO buildings (player_id, item_name, pos_x, pos_y) VALUES (?,?,?,?)",
              (PLAYER_ID, item_name, x, y))
    conn.commit()
    conn.close()

def get_buildings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT item_name, pos_x, pos_y FROM buildings WHERE player_id=? AND is_built=1",
              (PLAYER_ID,))
    rows = c.fetchall()
    conn.close()
    return rows

init_db()
player = load_player()