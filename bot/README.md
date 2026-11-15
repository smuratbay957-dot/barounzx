# Barounzx Telegram Bot

Skill yig'ish uchun Telegram bot (Python + aiogram 3). Sayt bilan bog'lanadi.

## Imkoniyatlar

- **Majburiy obuna**: kanal (`@megaskils`) va guruh (`@megaskills`).
- **Free Skill**: admin `/freeskill <miqdor>` yozsa kanalda chiroyli karta + tugma chiqadi.
  Tugma bosilganda foydalanuvchi skill oladi (bir marta). Guruhga va barcha
  foydalanuvchilarga e'lon boradi.
- **Rarity itemlar**: admin `/items <nomi>, <narx>, <rarity>, <soni>, <skill>` yaratadi.
  Guruhda "Sotib olish" tugmasi bilan chiqadi. Sotilganda soni kamayadi, skill beriladi.
- **Tanga (🪙)**: o'yin valyutasi. Sayt bilan umumiy.
- **Telegram Stars (⭐)**: `1 Star = 10 tanga`. `/star` orqali tanga olinadi.
- **Hisobni ulash**: `/login` — saytdagi ism va parol bilan. Parol unutilsa saytdan tiklanadi.

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
| `/profile` `/skills` `/balance` | hamma | profil / skill / tanga |
| `/shop` | hamma | do'kon |
| `/star` | hamma | Stars orqali tanga |
| `/login` | hamma | sayt hisobini ulash |
| `/daily` | hamma | kunlik bonus |
| `/freeskill <miqdor>` | admin | Free Skill e'loni |
| `/items <nomi>, <narx>, <rarity>, <soni>, <skill>` | admin | item yaratish |
| `/broadcast <xabar>` | admin | hammaga xabar |
| `/give <tg_id> <tanga> <skill>` | admin | foydalanuvchiga berish |
| `/stats` | admin | statistika |

Misol:
```
/freeskill 5
/items Ninza qilish, 1200, epic, 10, 2
```

## Bot sozlamalari (BotFather)

1. Botni kanal (`@megaskils`) va guruh (`@megaskills`)ga **admin** qiling.
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

## Sayt bilan bog'lash (keyingi qadam)

Hozircha `SITE_API_URL` bo'sh — `/login` "offline rejim"da ishlaydi. Backend
(PythonAnywhere) tayyor bo'lgach:

1. `.env` da `SITE_API_URL=https://<sizning>.pythonanywhere.com` ni yozing.
2. Backend quyidagi endpointni taqdim etishi kerak:

```
POST /api/login
Headers: X-API-Key: <SITE_API_KEY>
Body:    {"username": "...", "password": "..."}
Javob:   200 {"ok": true}   yoki   401 {"ok": false, "error": "Parol xato"}
```

3. Skillarni sinxronlash uchun (kelajakda):
```
POST /api/sync        # bot -> sayt
Body: {"username": "...", "skills": 12, "coins": 300}
```

## Xavfsizlik

- `.env` **hech qachon** GitHub'ga yuklanmaydi (`.gitignore` da).
- Token chatda oshkor bo'lgan bo'lsa, **@BotFather → /revoke** qilib yangisini oling.
- Parolni bazada saqlamang — faqat backend orqali tekshiring.
