import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def validate_init_data(init_data, bot_token, max_age=86400):
    """Telegram Web App initData ni bot token bilan tekshiradi."""
    if not init_data or not bot_token:
        return None
    try:
        pairs = parse_qsl(init_data, keep_blank_values=True)
    except Exception:
        return None
    data = dict(pairs)
    received = data.pop("hash", None)
    if not received:
        return None
    check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(pairs) if key != "hash"
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    expected = hmac.new(
        secret_key, check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, received):
        return None
    try:
        auth_date = int(data.get("auth_date") or 0)
    except (TypeError, ValueError):
        return None
    if auth_date and time.time() - auth_date > max_age:
        return None
    try:
        user = json.loads(data.get("user") or "{}")
    except Exception:
        return None
    if not isinstance(user, dict) or not user.get("id"):
        return None
    return user
