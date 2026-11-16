# Barounzx Telegram Bot

SP yig'ish uchun Telegram bot (Python + aiogram 3). Sayt bilan bog'lanadi.

## Imkoniyatlar

- **Majburiy obuna**: kanal (`@megaskils`) va guruh (`@megaskillsyour`).
- **Free SP**: admin `/freeskill <miqdor>` yozsa kanalda chiroyli karta + tugma chiqadi.
  Tugma bosilganda foydalanuvchi SP oladi (bir marta). Guruhga va barcha
  foydalanuvchilarga e'lon boradi.
- **Rarity itemlar**: admin `/items <nomi>, <narx>, <rarity>, <soni>, <sp>` yaratadi.
  Guruhda "Sotib olish" tugmasi bilan chiqadi. Sotilganda soni kamayadi, SP beriladi.
- **Tanga (🪙)**: o'yin valyutasi (bot ichida; sayt tangalari hozircha alohida).
- **Telegram Stars (⭐)**: `1 Star = 10 tanga`. `/star` orqali tanga olinadi.
- **Hisobni ulash**: saytda **Sozlamalar → Telegram ulash** → kodni `/ulash <kod>` ga yuborish.
  `1 SP = 20 XP`; SP/XP/Level sayt va bot o'rtasida sinxron bo'ladi.

## O'rnatish

```bash
cd bot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` ni `.env` ga ko'chirib, qiymatlarni to'ldiring (token, admin id, kanal/guruh).

```bash
cp .env.example .env
python main.py
```

## Buyruqlar

| Buyruq | Kim | Tavsif |
|---|---|---|
| `/start` | hamma | boshlash + obuna |
| `/profile` `/skills` `/balance` | hamma | profil / SP / tanga |
| `/shop` | hamma | do'kon |
| `/star` | hamma | Stars orqali tanga |
| `/ulash <kod>` | hamma | sayt hisobini ulash |
| `/uzish` | hamma | sayt hisobini uzish |
| `/daily` | hamma | kunlik bonus |
| `/freeskill <miqdor>` | admin | Free SP e'loni |
| `/items <nomi>, <narx>, <rarity>, <soni>, <sp>` | admin | item yaratish |
| `/broadcast <xabar>` | admin | hammaga xabar |
| `/give <tg_id> <tanga> <sp>` | admin | foydalanuvchiga berish |
| `/stats` | admin | statistika |

Misol:
```
/freeskill 5
/items Ninza qilish, 1200, epic, 10, 2
```

## Bot sozlamalari (BotFather)

1. Botni kanal (`@megaskils`) va guruh (`@megaskillsyour`)ga **admin** qiling.
2. Guruhda bot **privacy** sozlamasini o'chiring (guruh xabarlarini ko'rishi uchun) yoki
   admin qiling.
3. Stars to'lovlari uchun qo'shimcha sozlash shart emas.

## PythonAnywhere (free plan) — proxy

Free planda tashqi internetga faqat PythonAnywhere proxy'si orqali chiqiladi.
`api.telegram.org` allowlist'da, lekin aiohttp to'g'ridan-to'g'ri ulanmoqchi bo'lib
`Network is unreachable` beradi. Yechim — `.env` da:

```
PROXY_URL=http://proxy.server:3128
```

Keyin bot proxy orqali ulanadi. (Paid planda `PROXY_URL` bo'sh qoldiriladi.)

## Sayt bilan bog'lash

Sayt va bot **bitta SQLite bazani** ishlatadi. PythonAnywhere'da baza:
`/home/zxmax/barounzx/bot/barounzx_bot.db` (bot ham, web app ham shu faylni ochadi).

- Sayt: `SITE_URL=https://smuratbay957-dot.github.io/barounzx/`
- API (web app): `https://zxmax.pythonanywhere.com`

Ulash oqimi:
1. Saytda **Sozlamalar → Telegram ulash → Kod olish**.
2. Botga `/ulash <6 xonali kod>` yuboriladi.
3. Sayt kodni tekshirib, SP/XP/Level'ni serverdan oladi.

API endpointlari (`deploy/pa_api_wsgi.py`):
```
GET  /api/health
POST /api/link/start   {"username": "..."}      -> {"ok", "code", "token"}
GET  /api/link/status?code=123456               -> {"ok", "linked", ...}
POST /api/state        {"token","tg_id","xp","level"}
GET  /api/state?token=...&tg_id=...             -> {"ok","skills","xp","level"}
POST /api/raise        {"token","tg_id"}        -> 1 SP -> +20 XP
POST /api/unlink       {"token","tg_id"}
```

## Xavfsizlik

- `.env` **hech qachon** GitHub'ga yuklanmaydi (`.gitignore` da).
- Token chatda oshkor bo'lgan bo'lsa, **@BotFather → /revoke** qilib yangisini oling.
- Sayt paroli backendga yuborilmaydi; hisob faqat 6 xonali kod orqali ulanadi.
