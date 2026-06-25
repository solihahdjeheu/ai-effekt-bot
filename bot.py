"""
AI Effekt Bot — Telegram bot
-----------------------------
Foydalanuvchi rasm yuboradi -> bot effekt turini so'raydi -> Hugging Face
Inference API orqali rasmni qayta ishlaydi -> natijani qaytaradi.

Talab qilinadigan ENV o'zgaruvchilar (Render.com "Environment" bo'limida qo'shiladi):
  BOT_TOKEN   - @BotFather'dan olingan token
  HF_TOKEN    - huggingface.co/settings/tokens dan olingan "Read" token (bepul)

Ishga tushirish (lokal sinov uchun):
  pip install -r requirements.txt
  export BOT_TOKEN=...
  export HF_TOKEN=...
  python bot.py
"""

import asyncio
import io
import logging
import os
from threading import Thread

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
    CallbackQuery,
)
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai-effekt-bot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable o'rnatilmagan!")

# ---------------------------------------------------------------------------
# Effektlar ro'yxati: nom -> Hugging Face model id
# DIQQAT: Hugging Face'dagi modellar tez-tez o'zgaradi/o'chiriladi. Quyidagi
# model ID'lar namuna sifatida berilgan — ishlatishdan oldin
# huggingface.co/models sahifasida "image-to-image" filtri bilan qidirib,
# "Inference API" yoqilgan (aktiv) modelni tanlab, shu yerga shu model
# nomini (masalan "username/model-nomi") qo'ying.
# ---------------------------------------------------------------------------
EFFECTS = {
    "anime": {
        "label": "🌸 Anime",
        "model": "instruction-tuning-sd/cartoonizer",
    },
    "sketch": {
        "label": "✏️ Qalam chizma",
        "model": "lllyasviel/sd-controlnet-scribble",
    },
    "oldphoto": {
        "label": "🕰 Eski foto",
        "model": "microsoft/swin2SR-classical-sr-x2-64",
    },
}

HF_API_URL = "https://api-inference.huggingface.co/models/{model}"

# foydalanuvchi yuborgan oxirgi rasmni xotirada saqlash (oddiy holatlar uchun)
user_last_photo: dict[int, bytes] = {}


def build_effect_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for key, info in EFFECTS.items():
        rows.append([InlineKeyboardButton(text=info["label"], callback_data=f"effect:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def call_huggingface(model: str, image_bytes: bytes) -> bytes:
    """Hugging Face Inference API'ga rasmni yuborib, natija rasmni qaytaradi."""
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/octet-stream",
    }
    url = HF_API_URL.format(model=model)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=image_bytes, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 503:
                # model "cold start" bo'lib turgan bo'lishi mumkin, biroz kutib qayta urinamiz
                await asyncio.sleep(8)
                async with session.post(url, headers=headers, data=image_bytes, timeout=aiohttp.ClientTimeout(total=60)) as resp2:
                    resp2.raise_for_status()
                    return await resp2.read()
            resp.raise_for_status()
            return await resp.read()


async def on_start(message: Message):
    await message.answer(
        "Salom! 👋\n\n"
        "Menga bir dona *selfie* yoki rasm yuboring, keyin qaysi effekt kerakligini tanlaysiz.\n\n"
        "Effektlar: 🌸 Anime, ✏️ Qalam chizma, 🕰 Eski foto",
        parse_mode="Markdown",
    )


async def on_photo(message: Message, bot: Bot):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    user_last_photo[message.from_user.id] = buf.getvalue()

    await message.answer(
        "Qaysi effektni qo'llaymiz?",
        reply_markup=build_effect_keyboard(),
    )


async def on_effect_chosen(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    key = callback.data.split(":", 1)[1]
    effect = EFFECTS.get(key)

    if not effect:
        await callback.answer("Noma'lum effekt", show_alert=True)
        return

    image_bytes = user_last_photo.get(user_id)
    if not image_bytes:
        await callback.answer("Avval rasm yuboring!", show_alert=True)
        return

    await callback.answer()
    progress_msg = await callback.message.answer("⏳ Ishlanmoqda, biroz kuting (10-30 soniya)...")

    try:
        result_bytes = await call_huggingface(effect["model"], image_bytes)
        photo_file = BufferedInputFile(result_bytes, filename="natija.png")
        await callback.message.answer_photo(
            photo_file,
            caption=f"{effect['label']} effekti tayyor ✅",
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("HF inference error")
        await callback.message.answer(
            "❌ Xatolik yuz berdi. Model hozir band bo'lishi mumkin, biroz keyin qaytadan urinib ko'ring.\n\n"
            f"Texnik tafsilot: {exc}"
        )
    finally:
        await progress_msg.delete()


async def on_other(message: Message):
    await message.answer("Iltimos, menga rasm (foto) yuboring 📸")


def start_keepalive_server():
    """Render.com bepul tarifda 'Web Service' portni kutadi — shu sababli
    juda oddiy HTTP server ochib qo'yamiz, bot polling esa alohida ishlaydi."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"AI Effekt Bot ishlayapti.")

        def log_message(self, *args):
            return  # konsolni keraksiz log bilan to'ldirmaslik uchun

    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(on_start, CommandStart())
    dp.message.register(on_photo, F.photo)
    dp.callback_query.register(on_effect_chosen, F.data.startswith("effect:"))
    dp.message.register(on_other)

    log.info("Bot ishga tushdi, polling boshlandi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    Thread(target=start_keepalive_server, daemon=True).start()
    asyncio.run(main())
