# ============================================================
#  Barounzx bot - yordamchi funksiyalar
# ============================================================
from config import CHANNEL_USERNAME, GROUP_USERNAME, ADMIN_ID


async def _is_member(bot, chat, user_id) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat, user_id=user_id)
        status = member.status
        if status in ("creator", "administrator", "member"):
            return True
        if status == "restricted":
            return bool(getattr(member, "is_member", False))
        return False
    except Exception:
        # Bot kanal/guruhda admin bo'lmasa yoki chat topilmasa
        return False


async def is_subscribed(bot, user_id) -> bool:
    """Kanalga VA guruhga obuna bo'lishi shart."""
    channel = await _is_member(bot, CHANNEL_USERNAME, user_id)
    group = await _is_member(bot, GROUP_USERNAME, user_id)
    return channel and group


def is_admin(user_id) -> bool:
    return user_id == ADMIN_ID
