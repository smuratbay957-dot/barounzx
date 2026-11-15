# ============================================================
#  Sayt bilan bog'lanish (kelajakda PythonAnywhere backend)
#  SITE_API_URL bo'sh bo'lsa -> offline rejim (login tekshirilmaydi).
# ============================================================
import aiohttp

from config import SITE_API_URL, SITE_API_KEY


async def verify_site_login(username: str, password: str):
    """Qaytaradi: (ok: bool, info: str)."""
    if not SITE_API_URL:
        # Backend hali ulanmagan: offline rejimda qabul qilamiz.
        return True, "offline"

    url = SITE_API_URL.rstrip("/") + "/api/login"
    headers = {"X-API-Key": SITE_API_KEY} if SITE_API_KEY else {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json={"username": username, "password": password},
                headers=headers, timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 200 and data.get("ok"):
                    return True, "ok"
                return False, data.get("error", "Login yoki parol xato.")
    except Exception as exc:  # noqa: BLE001
        return False, f"Server bilan aloqa yo'q: {exc}"
