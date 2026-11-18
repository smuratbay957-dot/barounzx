# ============================================================
#  Barounzx - sayt <-> bot API (PythonAnywhere WSGI)
#  Sayt GitHub Pages'da, bot PA console'da ishlaydi. Ikkisi shu API
#  va umumiy SQLite fayli orqali bog'lanadi.
#
#  PA WSGI fayliga yoziladi:
#      import sys
#      sys.path.insert(0, "/home/zxmax/barounzx/deploy")
#      from pa_api_wsgi import application
# ============================================================
import json
import os
import sys
from urllib.parse import parse_qs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOT_DIR = os.path.join(BASE_DIR, "bot")
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

import database as db  # noqa: E402
from config import BOT_TOKEN  # noqa: E402
import webapp_auth  # noqa: E402

db.init_db()

CORS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type"),
    ("Access-Control-Max-Age", "86400"),
]


def _json(start_response, status, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(data))),
    ] + CORS
    start_response(status, headers)
    return [data]


def _body(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except (TypeError, ValueError):
        length = 0
    if length <= 0:
        return {}
    raw = environ["wsgi.input"].read(length)
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _query(environ):
    return {k: v[0] for k, v in parse_qs(environ.get("QUERY_STRING", "")).items()}


def application(environ, start_response):
    method = (environ.get("REQUEST_METHOD") or "GET").upper()
    path = (environ.get("PATH_INFO") or "/").rstrip("/") or "/"

    if method == "OPTIONS":
        start_response("204 No Content", CORS)
        return [b""]

    try:
        if path == "/api/health":
            return _json(start_response, "200 OK", {"ok": True, "service": "barounzx-api"})

        # --- Telegram Web App: initData orqali avtomatik ulash ---
        if path == "/api/webapp/auth" and method == "POST":
            data = _body(environ)
            user = webapp_auth.validate_init_data(data.get("init_data"), BOT_TOKEN)
            if not user:
                return _json(start_response, "401 Unauthorized",
                             {"ok": False, "error": "initData yaroqsiz"})
            res = db.link_webapp(
                user.get("id"), user.get("username"), user.get("first_name")
            )
            if not res:
                return _json(start_response, "500 Internal Server Error",
                             {"ok": False, "error": "ulash muvaffaqiyatsiz"})
            return _json(start_response, "200 OK", {"ok": True, **res})

        if path == "/api/items" and method == "GET":
            return _json(start_response, "200 OK",
                         {"ok": True, "items": db.list_items()})

        if path in ("/api/daily", "/api/spin", "/api/buy") and method == "POST":
            data = _body(environ)
            token = data.get("token")
            if path == "/api/daily":
                res = db.webapp_daily(token)
            elif path == "/api/spin":
                res = db.webapp_spin(token)
            else:
                res = db.webapp_buy(token, data.get("item_id"))
            if res is None:
                return _json(start_response, "401 Unauthorized",
                             {"ok": False, "error": "token xato"})
            if res.get("error"):
                return _json(start_response, "200 OK", {"ok": False, **res})
            return _json(start_response, "200 OK", {"ok": True, **res})

        # --- Sayt kod oladi ---
        if path == "/api/link/start" and method == "POST":
            data = _body(environ)
            username = str(data.get("username") or "").strip()
            if not username:
                return _json(start_response, "400 Bad Request",
                             {"ok": False, "error": "username kerak"})
            res = db.create_link_code(username)
            if not res:
                return _json(start_response, "500 Internal Server Error",
                             {"ok": False, "error": "kod yaratilmadi"})
            return _json(start_response, "200 OK", {"ok": True, **res})

        # --- Sayt ulanish holatini tekshiradi ---
        if path == "/api/link/status" and method == "GET":
            code = (_query(environ).get("code") or "").strip()
            row = db.get_link_status(code) if code else None
            if not row:
                return _json(start_response, "404 Not Found",
                             {"ok": False, "error": "kod topilmadi"})
            linked = bool(row.get("used"))
            payload = {
                "ok": True,
                "linked": linked,
                "site_username": row.get("site_username"),
            }
            if linked:
                payload.update({
                    "tg_id": row.get("tg_id"),
                    "tg_username": row.get("tg_username"),
                })
            return _json(start_response, "200 OK", payload)

        # --- Sayt holatni o'qiydi / yozadi ---
        if path == "/api/state" and method == "GET":
            q = _query(environ)
            state = db.get_site_state(q.get("tg_id"), q.get("token"))
            if not state:
                return _json(start_response, "401 Unauthorized",
                             {"ok": False, "error": "token xato"})
            return _json(start_response, "200 OK", {"ok": True, **state})

        if path == "/api/state" and method == "POST":
            data = _body(environ)
            state = db.set_site_state(
                data.get("tg_id"), data.get("token"), data.get("xp"), data.get("level"),
                coins=data.get("coins"), skills=data.get("skills"),
            )
            if not state:
                return _json(start_response, "401 Unauthorized",
                             {"ok": False, "error": "token xato"})
            return _json(start_response, "200 OK", {"ok": True, **state})

        # --- Tanga o'zgarishi (site <-> bot bitta bazada) ---
        if path == "/api/coins" and method == "POST":
            data = _body(environ)
            state = db.adjust_coins(
                data.get("tg_id"), data.get("token"), data.get("delta")
            )
            if not state:
                return _json(start_response, "401 Unauthorized",
                             {"ok": False, "error": "token xato"})
            return _json(start_response, "200 OK", {"ok": True, **state})

        # --- SP ko'tarish (1 SP -> 20 XP) ---
        if path == "/api/raise" and method == "POST":
            data = _body(environ)
            res = db.raise_sp(data.get("tg_id"), data.get("token"))
            if res is None:
                return _json(start_response, "401 Unauthorized",
                             {"ok": False, "error": "token xato"})
            if res.get("error") == "no_sp":
                return _json(start_response, "200 OK", {"ok": False, **res})
            return _json(start_response, "200 OK", {"ok": True, **res})

        # --- Saytni uzish ---
        if path == "/api/unlink" and method == "POST":
            data = _body(environ)
            ok = db.unlink_site(data.get("tg_id"), data.get("token"))
            return _json(start_response, "200 OK", {"ok": bool(ok)})

        return _json(start_response, "404 Not Found",
                     {"ok": False, "error": "not found"})
    except Exception as exc:  # noqa: BLE001
        return _json(start_response, "500 Internal Server Error",
                     {"ok": False, "error": str(exc)})
