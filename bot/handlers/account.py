# ============================================================
#  Sayt hisobini ulash: /login (ism + parol -> backend tekshiradi)
# ============================================================
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from site_api import verify_site_login

router = Router()


class Login(StatesGroup):
    username = State()
    password = State()


@router.message(Command("login"))
async def cmd_login(message: Message, state: FSMContext):
    user = db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    if user.get("site_linked"):
        await message.answer(
            f"🔗 Siz allaqachon ulangansiz: <b>{user['site_username']}</b>"
        )
        return
    await state.set_state(Login.username)
    await message.answer(
        "🔗 <b>Sayt hisobini ulash</b>\n\n"
        "Saytdagi <b>ismingizni</b> kiriting:",
        reply_markup=kb.cancel_kb(),
    )


@router.message(Login.username)
async def login_username(message: Message, state: FSMContext):
    await state.update_data(username=(message.text or "").strip())
    await state.set_state(Login.password)
    await message.answer("🔒 Endi <b>parolingizni</b> kiriting:\n\n"
                         "<i>Parol xavfsizlik uchun o'chiriladi.</i>")


@router.message(Login.password)
async def login_password(message: Message, state: FSMContext):
    data = await state.get_data()
    username = data.get("username", "")
    password = message.text or ""
    try:
        await message.delete()
    except Exception:
        pass

    ok, info = await verify_site_login(username, password)
    if not ok:
        await state.clear()
        await message.answer(f"❌ {info}\n\nQaytadan urinish uchun /login yuboring.")
        return

    db.link_site_account(message.from_user.id, username)
    await state.clear()
    note = " (offline rejim)" if info == "offline" else ""
    await message.answer(
        f"✅ Hisob ulandi: <b>{username}</b>{note}\n\n"
        "Endi botdagi skill va tangalar saytingiz bilan bog'lanadi."
    )


@router.callback_query(F.data == "login:cancel")
async def login_cancel(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.answer("Bekor qilindi.")
    try:
        await cq.message.edit_text("❌ Ulanish bekor qilindi.")
    except Exception:
        pass
