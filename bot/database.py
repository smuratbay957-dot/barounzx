# ============================================================
#  Barounzx bot - ma'lumotlar bazasi (SQLite)
# ============================================================
import random
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

from config import DAILY_COINS, DB_PATH, XP_PER_SKILL

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id         INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    skills        INTEGER NOT NULL DEFAULT 0,
    coins         INTEGER NOT NULL DEFAULT 0,
    site_username TEXT,
    site_linked   INTEGER NOT NULL DEFAULT 0,
    site_token    TEXT,
    xp            INTEGER NOT NULL DEFAULT 0,
    level         INTEGER NOT NULL DEFAULT 1,
    last_daily    TEXT,
    streak        INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS link_codes (
    code          TEXT PRIMARY KEY,
    site_username TEXT NOT NULL,
    site_token    TEXT NOT NULL,
    tg_id         INTEGER,
    used          INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at    TEXT NOT NULL
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
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as c:
        c.executescript(SCHEMA)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()}
        if "site_token" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN site_token TEXT")
        if "xp" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN xp INTEGER NOT NULL DEFAULT 0")
        if "level" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN level INTEGER NOT NULL DEFAULT 1")


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


# ---------------- Sayt <-> bot ulash ----------------
def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _xp_to_next(level):
    return 100 + (max(1, level) - 1) * 50


def create_link_code(site_username, ttl_minutes=15):
    """Sayt uchun 6 xonali kod yaratadi: {'code', 'token', 'expires_at'}."""
    site_username = (site_username or "").strip()
    if not site_username:
        return None
    token = secrets.token_urlsafe(24)
    expires = (_now() + timedelta(minutes=ttl_minutes)).isoformat(timespec="seconds")
    with db() as c:
        c.execute("DELETE FROM link_codes WHERE site_username=? AND used=0", (site_username,))
        for _ in range(12):
            code = f"{secrets.randbelow(1000000):06d}"
            try:
                c.execute(
                    "INSERT INTO link_codes (code, site_username, site_token, expires_at) VALUES (?,?,?,?)",
                    (code, site_username, token, expires),
                )
                return {"code": code, "token": token, "expires_at": expires}
            except sqlite3.IntegrityError:
                continue
    return None


def get_link_status(code):
    with db() as c:
        row = c.execute(
            "SELECT lc.*, u.username AS tg_username FROM link_codes lc "
            "LEFT JOIN users u ON u.tg_id = lc.tg_id WHERE lc.code=?",
            (code,),
        ).fetchone()
        return dict(row) if row else None


def link_by_code(code, tg_id):
    """Kodni tg_id ga bog'laydi. Muvaffaqiyatli: {'site_username': ...}."""
    now = _now().isoformat(timespec="seconds")
    with db() as c:
        row = c.execute(
            "SELECT * FROM link_codes WHERE code=? AND used=0", (code,)
        ).fetchone()
        if not row or row["expires_at"] < now:
            return None
        # Bitta sayt hisobiga faqat bitta Telegram bog'lanadi.
        c.execute(
            "UPDATE users SET site_linked=0, site_username=NULL, site_token=NULL "
            "WHERE site_username=? AND tg_id<>? AND site_linked=1",
            (row["site_username"], tg_id),
        )
        c.execute(
            "UPDATE users SET site_username=?, site_linked=1, site_token=? WHERE tg_id=?",
            (row["site_username"], row["site_token"], tg_id),
        )
        c.execute("UPDATE link_codes SET used=1, tg_id=? WHERE code=?", (tg_id, code))
        return {"site_username": row["site_username"]}


def unlink_user(tg_id):
    with db() as c:
        c.execute(
            "UPDATE users SET site_linked=0, site_username=NULL, site_token=NULL WHERE tg_id=?",
            (tg_id,),
        )


def unlink_site(tg_id, token):
    with db() as c:
        cur = c.execute(
            "UPDATE users SET site_linked=0, site_username=NULL, site_token=NULL "
            "WHERE tg_id=? AND site_token=?",
            (tg_id, token),
        )
        return cur.rowcount > 0


def get_site_state(tg_id, token):
    try:
        tg_id = int(tg_id)
    except (TypeError, ValueError):
        return None
    with db() as c:
        row = c.execute(
            "SELECT * FROM users WHERE tg_id=? AND site_token=?", (tg_id, token)
        ).fetchone()
        if not row:
            return None
        return {
            "tg_id": row["tg_id"],
            "site_username": row["site_username"],
            "skills": row["skills"],
            "xp": row["xp"],
            "level": row["level"],
            "coins": row["coins"],
        }


def set_site_state(tg_id, token, xp, level, coins=None, skills=None):
    try:
        tg_id = int(tg_id)
        xp = max(0, int(xp or 0))
        level = max(1, int(level or 1))
        coins = max(0, int(coins)) if coins is not None else None
        skills = max(0, int(skills)) if skills is not None else None
    except (TypeError, ValueError):
        return None
    with db() as c:
        row = c.execute(
            "SELECT * FROM users WHERE tg_id=? AND site_token=?", (tg_id, token)
        ).fetchone()
        if not row:
            return None
        new_coins = row["coins"] if coins is None else coins
        new_skills = row["skills"] if skills is None else skills
        c.execute(
            "UPDATE users SET xp=?, level=?, coins=?, skills=? WHERE tg_id=?",
            (xp, level, new_coins, new_skills, tg_id),
        )
        return {
            "tg_id": tg_id,
            "site_username": row["site_username"],
            "skills": new_skills,
            "xp": xp,
            "level": level,
            "coins": new_coins,
        }


def adjust_coins(tg_id, token, delta):
    """Tangalarni atomik tarzda o'zgartiradi (sayt va bot umumiy baza)."""
    try:
        tg_id = int(tg_id)
        delta = int(delta)
    except (TypeError, ValueError):
        return None
    with db() as c:
        row = c.execute(
            "SELECT * FROM users WHERE tg_id=? AND site_token=?", (tg_id, token)
        ).fetchone()
        if not row:
            return None
        coins = max(0, row["coins"] + delta)
        c.execute("UPDATE users SET coins=? WHERE tg_id=?", (coins, tg_id))
        return {
            "tg_id": tg_id,
            "site_username": row["site_username"],
            "skills": row["skills"],
            "xp": row["xp"],
            "level": row["level"],
            "coins": coins,
        }


def raise_sp(tg_id, token):
    """1 SP -> +XP_PER_SKILL XP. Natija: state yoki {'error': 'no_sp'} / None."""
    try:
        tg_id = int(tg_id)
    except (TypeError, ValueError):
        return None
    with db() as c:
        row = c.execute(
            "SELECT * FROM users WHERE tg_id=? AND site_token=?", (tg_id, token)
        ).fetchone()
        if not row:
            return None
        if row["skills"] <= 0:
            return {
                "error": "no_sp",
                "tg_id": tg_id,
                "site_username": row["site_username"],
                "skills": row["skills"],
                "xp": row["xp"],
                "level": row["level"],
                "coins": row["coins"],
            }
        skills = row["skills"] - 1
        xp = row["xp"] + XP_PER_SKILL
        level = row["level"]
        while xp >= _xp_to_next(level):
            xp -= _xp_to_next(level)
            level += 1
        c.execute(
            "UPDATE users SET skills=?, xp=?, level=? WHERE tg_id=?",
            (skills, xp, level, tg_id),
        )
        return {
            "tg_id": tg_id,
            "site_username": row["site_username"],
            "skills": skills,
            "xp": xp,
            "level": level,
            "coins": row["coins"],
        }


# ---------------- Telegram Web App ----------------
def _web_state(row, **overrides):
    data = {
        "tg_id": row["tg_id"],
        "site_username": row["site_username"],
        "skills": row["skills"],
        "xp": row["xp"],
        "level": row["level"],
        "coins": row["coins"],
    }
    data.update(overrides)
    return data


def _apply_levels(xp, level, coins):
    while xp >= _xp_to_next(level):
        xp -= _xp_to_next(level)
        level += 1
        coins += 25 + level * 10
    return xp, level, coins


def link_webapp(tg_id, username=None, first_name=None):
    """initData tasdiqlangandan keyin Telegram foydalanuvchisini ulaydi."""
    try:
        tg_id = int(tg_id)
    except (TypeError, ValueError):
        return None
    get_or_create_user(tg_id, username, first_name)
    token = secrets.token_urlsafe(24)
    name = str(username or first_name or tg_id).lstrip("@")
    with db() as c:
        c.execute(
            "UPDATE users SET site_linked=1, site_username=?, site_token=?, "
            "username=?, first_name=? WHERE tg_id=?",
            (name, token, username, first_name, tg_id),
        )
    return {"token": token, **get_site_state(tg_id, token)}


def webapp_daily(token):
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE site_token=?", (token,)).fetchone()
        if not row:
            return None
        today = date.today().isoformat()
        if row["last_daily"] == today:
            return {"error": "already", **_web_state(row)}
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        streak = row["streak"] + 1 if row["last_daily"] == yesterday else 1
        reward = DAILY_COINS + streak * 5
        xp, level, coins = _apply_levels(
            row["xp"] + 25, row["level"], row["coins"] + reward
        )
        c.execute(
            "UPDATE users SET coins=?, xp=?, level=?, last_daily=?, streak=? WHERE tg_id=?",
            (coins, xp, level, today, streak, row["tg_id"]),
        )
        return {
            **_web_state(row, coins=coins, xp=xp, level=level),
            "reward": reward,
            "streak": streak,
        }


def webapp_spin(token):
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE site_token=?", (token,)).fetchone()
        if not row:
            return None
        if row["coins"] < 50:
            return {"error": "no_money", **_web_state(row)}
        win = random.choices(
            [0, 10, 20, 50, 100, 200], weights=[10, 25, 25, 20, 15, 5]
        )[0]
        xp, level, coins = _apply_levels(
            row["xp"] + 20, row["level"], row["coins"] - 50 + win
        )
        c.execute(
            "UPDATE users SET coins=?, xp=?, level=? WHERE tg_id=?",
            (coins, xp, level, row["tg_id"]),
        )
        return {**_web_state(row, coins=coins, xp=xp, level=level), "win": win}


def webapp_buy(token, item_id):
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE site_token=?", (token,)).fetchone()
    if not row:
        return None
    res = buy_item(row["tg_id"], item_id)
    if not res or res.get("error"):
        return res
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE tg_id=?", (row["tg_id"],)).fetchone()
        xp, level, coins = _apply_levels(row["xp"] + 15, row["level"], row["coins"])
        c.execute(
            "UPDATE users SET xp=?, level=?, coins=? WHERE tg_id=?",
            (xp, level, coins, row["tg_id"]),
        )
    return {
        **_web_state(row, xp=xp, level=level, coins=coins),
        "gained": res["gained"],
        "spent": res["spent"],
    }


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
