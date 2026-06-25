# AI Effekt Bot — to'liq yo'riqnoma

Bu bot foydalanuvchidan rasm qabul qiladi, qaysi effekt kerakligini so'raydi
(Anime / Qalam chizma / Eski foto), Hugging Face AI orqali qayta ishlaydi va
natijani qaytaradi.

---

## 1-qadam: Telegram bot tokenini olish

1. Telegramda **@BotFather** ni topib, `/start` yozing.
2. `/newbot` buyrug'ini yuboring.
3. Bot uchun nom va username so'raydi (username `bot` bilan tugashi kerak,
   masalan `AbbosEffektBot`).
4. BotFather sizga shunday token beradi:
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   — shu tokenni saqlab qo'ying, bu `BOT_TOKEN`.

## 2-qadam: Hugging Face tokenini olish (bepul)

1. [huggingface.co](https://huggingface.co) saytida ro'yxatdan o'ting.
2. Profil → **Settings → Access Tokens** ga kiring.
3. "New token" → turini **Read** qilib yarating.
4. Token nusxasini saqlang — bu `HF_TOKEN`.

> Eslatma: Hugging Face'ning bepul Inference API'si ba'zan modelni "uyqudan
> uyg'otish" uchun birinchi so'rovda 10-30 soniya kechikadi — bu normal holat,
> kodda shu holat uchun avtomatik qayta urinish (retry) qilingan.

## 3-qadam: Render.com'da bepul hosting

1. [render.com](https://render.com) da ro'yxatdan o'ting (GitHub orqali kirish qulay).
2. Avval shu loyihani **GitHub'ga** yuklang:
   - GitHub'da yangi repository yarating (masalan `ai-effekt-bot`)
   - Shu papkadagi barcha fayllarni (`bot.py`, `requirements.txt`) shu repoga yuklang
3. Render dashboard'da **New → Web Service** tanlang.
4. GitHub repongizni ulang.
5. Sozlamalar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** Free
6. **Environment** bo'limida 2 ta o'zgaruvchi qo'shing:
   - `BOT_TOKEN` = (1-qadamdagi token)
   - `HF_TOKEN` = (2-qadamdagi token)
7. "Create Web Service" bosing — bir necha daqiqada bot ishga tushadi.

## 4-qadam: Sinash

Telegramda botingizni topib `/start` yozing, keyin bir dona selfie yuboring va
effekt tanlang.

---

## Modellarni almashtirish / yangilarini qo'shish

`bot.py` faylidagi `EFFECTS` lug'atida har bir effekt uchun Hugging Face model
nomi yozilgan. Agar biror model ishlamasa (o'chirilgan/band bo'lsa):

1. [huggingface.co/models](https://huggingface.co/models) ga kiring
2. Chap tomondan **Tasks → Image-to-Image** filtrini tanlang
3. "Inference API" yoqilgan modelni tanlab, uning nomini nusxalang
   (masalan `username/model-nomi`)
4. `bot.py` ichida shu nomni almashtiring, GitHub'ga qayta yuklang — Render
   avtomatik qayta deploy qiladi.

## Bepul tarifning cheklovi

Render'ning bepul "Web Service"si 15 daqiqa harakatsiz qolsa "uxlab qoladi" va
keyingi xabarga 30-60 soniya kech javob beradi — bu normal, pullik tarifga
o'tmaguningizcha shunday ishlaydi.
