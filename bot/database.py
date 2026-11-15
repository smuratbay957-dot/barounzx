# ============================================================
#  Barounzx bot - ma'lumotlar bazasi (SQLite)
# ============================================================
import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id         INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    skills        INTEGER NOT NULL DEFAULT 0,
    coins         INTEGER NOT NULL DEFAULT 0,
    site_username TEXT,
    site_linked   INTEGER NOT NULL DEFAULT 0,
    last_daily    TEXT,
    streak        INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    price            INTEGER NOT NULL,
    rarity           TEXT NOT NULL,
    stock            INTEGER NOT NULL,
    skill_value      INTEGER NOT NULL,
    active           INTEGER NOT NULL DEFAULT 1,
    group_message_id INTEGER,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS purchases (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id         INTEGER NOT NULL,
    item_id       INTEGER NOT NULL,
    qty           INTEGER NOT NULL DEFAULT 1,
    unit_price    INTEGER NOT NULL,
    skills_gained INTEGER NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS freeskills (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    amount             INTEGER NOT NULL,
    channel_message_id INTEGER,
    active             INTEGER NOT NULL DEFAULT 1,
    created_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS freeskill_claims (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    freeskill_id  INTEGER NOT NULL,
    tg_id         INTEGER NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(freeskill_id, tg_id)
);

CREATE TABLE IF NOT EXISTS payments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER NOT NULL,
    stars      INTEGER NOT NULL,
    coins      INTEGER NOT NULL,
    payload    TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as c:
        c.executescript(SCHEMA)


# ---------------- Users ----------------
def get_user(tg_id):
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        return dict(row) if row else None


def get_or_create_user(tg_id, username=None, first_name=None):
    user = get_user(tg_id)
    if user:
        return user
    from config import START_COINS
    with db() as c:
        c.execute(
            "INSERT INTO users (tg_id, username, first_name, coins) VALUES (?, ?, ?, ?)",
            (tg_id, username, first_name, START_COINS),
        )
    return get_user(tg_id)


def all_users():
    with db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM users").fetchall()]


def count_users():
    with db() as c:
        return c.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]


def add_skills(tg_id, amount):
    with db() as c:
        c.execute("UPDATE users SET skills = skills + ? WHERE tg_id=?", (amount, tg_id))


def add_coins(tg_id, amount):
    with db() as c:
        c.execute("UPDATE users SET coins = coins + ? WHERE tg_id=?", (amount, tg_id))


def try_spend_coins(tg_id, amount):
    with db() as c:
        row = c.execute("SELECT coins FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not row or row["coins"] < amount:
            return False
        c.execute("UPDATE users SET coins = coins - ? WHERE tg_id=?", (amount, tg_id))
        return True


def set_daily(tg_id, day, streak):
    with db() as c:
        c.execute("UPDATE users SET last_daily=?, streak=? WHERE tg_id=?", (day, streak, tg_id))


def link_site_account(tg_id, site_username):
    with db() as c:
        c.execute(
            "UPDATE users SET site_username=?, site_linked=1 WHERE tg_id=?",
            (site_username, tg_id),
        )


# ---------------- Items ----------------
def create_item(name, price, rarity, stock, skill_value):
    with db() as c:
        cur = c.execute(
            "INSERT INTO items (name, price, rarity, stock, skill_value) VALUES (?,?,?,?,?)",
            (name, price, rarity, stock, skill_value),
        )
        return cur.lastrowid


def get_item(item_id):
    with db() as c:
        row = c.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        return dict(row) if row else None


def set_item_message(item_id, message_id):
    with db() as c:
        c.execute("UPDATE items SET group_message_id=? WHERE id=?", (message_id, item_id))


def list_items(active_only=True):
    with db() as c:
        q = "SELECT * FROM items"
        if active_only:
            q += " WHERE active=1"
        q += " ORDER BY id DESC"
        return [dict(r) for r in c.execute(q).fetchall()]


def buy_item(tg_id, item_id, qty=1):
    """Tanga yechadi, stock kamaytiradi, skill beradi. True/None qaytaradi."""
    with db() as c:
        item = c.execute("SELECT * FROM items WHERE id=? AND active=1", (item_id,)).fetchone()
        if not item or item["stock"] < qty:
            return None
        total = item["price"] * qty
        user = c.execute("SELECT coins FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not user or user["coins"] < total:
            return {"error": "no_money", "need": total, "have": user["coins"] if user else 0}
        gained = item["skill_value"] * qty
        c.execute("UPDATE users SET coins = coins - ?, skills = skills + ? WHERE tg_id=?",
                  (total, gained, tg_id))
        c.execute("UPDATE items SET stock = stock - ? WHERE id=?", (qty, item_id))
        c.execute(
            "INSERT INTO purchases (tg_id, item_id, qty, unit_price, skills_gained) VALUES (?,?,?,?,?)",
            (tg_id, item_id, qty, item["price"], gained),
        )
        new_stock = c.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()["stock"]
        return {"gained": gained, "spent": total, "stock": new_stock}


# ---------------- Free skills ----------------
def create_freeskill(amount, channel_message_id=None):
    with db() as c:
        cur = c.execute(
            "INSERT INTO freeskills (amount, channel_message_id) VALUES (?,?)",
            (amount, channel_message_id),
        )
        return cur.lastrowid


def set_freeskill_message(fs_id, message_id):
    with db() as c:
        c.execute("UPDATE freeskills SET channel_message_id=? WHERE id=?", (message_id, fs_id))


def get_freeskill(fs_id):
    with db() as c:
        row = c.execute("SELECT * FROM freeskills WHERE id=?", (fs_id,)).fetchone()
        return dict(row) if row else None


def claim_freeskill(fs_id, tg_id, amount):
    """Bir marta olish uchun. True = muvaffaqiyat, False = allaqachon olgan."""
    with db() as c:
        try:
            c.execute(
                "INSERT INTO freeskill_claims (freeskill_id, tg_id) VALUES (?,?)",
                (fs_id, tg_id),
            )
        except sqlite3.IntegrityError:
            return False
        c.execute("UPDATE users SET skills = skills + ? WHERE tg_id=?", (amount, tg_id))
        return True


# ---------------- Payments ----------------
def add_payment(tg_id, stars, coins, payload=None):
    with db() as c:
        c.execute(
            "INSERT INTO payments (tg_id, stars, coins, payload) VALUES (?,?,?,?)",
            (tg_id, stars, coins, payload),
        )


def stats():
    with db() as c:
        users = c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
        items = c.execute("SELECT COUNT(*) n FROM items WHERE active=1").fetchone()["n"]
        buys = c.execute("SELECT COUNT(*) n FROM purchases").fetchone()["n"]
        stars = c.execute("SELECT COALESCE(SUM(stars),0) s FROM payments").fetchone()["s"]
        return {"users": users, "items": items, "purchases": buys, "stars": stars}
