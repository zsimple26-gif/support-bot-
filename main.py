# bot.py — полностью рабочая версия aiogram 3.x + Flask
import asyncio
import logging
from typing import Optional
from flask import Flask
import os
import threading
import sys
import traceback
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ------------------- НАСТРОЙКИ ------------------- #
API_TOKEN = os.environ.get("BOT_API_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_API_TOKEN не задан в Environment Variables!")
bot = Bot(token=API_TOKEN)
SUPPORT_GROUP_ID = int(os.environ.get("SUPPORT_GROUP_ID", "0"))  # ID группы операторов
MASTER_OPERATOR_ID = int(os.environ.get("MASTER_OPERATOR_ID", "0"))  # твой ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Храним выбранных пользователей операторов: {operator_id: user_id}
active_users: dict[int, int] = {}

# ------------------- МЕНЮ ------------------- #
def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("😇 Мне нужна поддержка"))
    kb.add(KeyboardButton("💞 Поговорить с человеком"))
    kb.add(KeyboardButton("🗒️ Правила чата"))
    kb.add(KeyboardButton("✨ Частые вопросы"))
    return kb

def support_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Хочу поделиться кое чем 😍"))
    kb.add(KeyboardButton("Нужен совет 👀"))
    kb.add(KeyboardButton("Главное меню"))
    return kb

# ------------------- ТЕКСТЫ ------------------- #
welcome_text = (
    "Добро пожаловать, милый человек.\n\n"
    "Я здесь, чтобы помочь тебе мягко и без лишнего давления.\n\n"
    "Выбери, что тебе сейчас нужно ниже 👇\n\n"
    "Если вдруг что-то тревожит — я рядом 🤍"
)

support_intro = (
    "😇 Ты в разделе поддержки 💗\n\n"
    "Выбери, что тебе сейчас нужно:\n\n"
    "Мы рядом — поможем, поддержим, ответим 💞"
)

share_text = (
    "Привет, дорогой сердечконосец! 😘\n\n"
    "Если у тебя есть что-то, что хочется рассказать — секретик, радость, забавная история или просто мысль о любви 💌 — смело делись здесь!\n\n"
    "Наш бот — это твой дружелюбный амурчик 🏹: он выслушает, обнимет словом и иногда подмигнёт смайликом 😉.\n\n"
    "Немного правил, чтобы ваша любовь к словам была безопасной 💕:\n\n"
    "Пиши честно и с душой 🌸\n\n"
    "Не оскорбляй других ❤️‍🔥\n\n"
    "Спам и странные вещи оставь за дверью 🚪😅\n\n"
    "Добавь смайлик — амурчик обожает их! 😇\n\n"
    "Помни: каждый раз, когда делишься чем-то, ты словно посылаешь маленькое сердечко миру 💖.\n\n"
    "Не стесняйся — амурчик ждёт твоего сообщения! 🥰"
)

advice_text = (
    "Привет! 😇\n\n"
    "Если тебе нужна маленькая подсказка или секретный любовный лайфхак 🏹 — ты по адресу!\n\n"
    "Наш амурчик готов выслушать и дать совет с улыбкой и смайликом 😉💌.\n\n"
    "Пиши свой вопрос — и пусть любовь (и юмор) ведут тебя! 💕"
)

human_connect_text = (
    "Хорошо, минутку — сейчас подключу тебя к оператору ❤️\n\n"
    "Он самый человечный из всех, обещаю 😘\n\n"
    "И возможно даже окажется лучше меня 😁, хотя я ревную конечно 👿"
)

rules_text = (
    "💖 Правила нашего любовного бота поддержки 💖\n\n"
    "Привет, дорогой пользователь! 😇 Этот бот здесь, чтобы помогать тебе в любых вопросах… и иногда даже подбрасывать романтики 💌. Но чтобы наша любовь (и чат) была чистой и счастливой, давай договоримся о паре правил:\n\n"
    "1. Будь вежливым и доброжелательным 🌸\n"
    "Мы здесь, чтобы дарить ❤️, а не 💔. Никаких обидных слов и грубости. Даже если ты влюблен в Wi-Fi больше, чем в нас 😉.\n\n"
    "2. Пиши по теме ✍️\n"
    "Бот готов помочь, но не умеет читать мысли 😅. Чем яснее вопрос — тем быстрее и романтичнее ответ 💌.\n\n"
    "3. Не спамь 🚫\n"
    "Мы любим внимание, но бот — не глупышка-папоротник 🌱. Одно сообщение в минуту — это идеально.\n\n"
    "4. Без запрещённого контента ❌\n"
    "Любовь — это прекрасно, а вот оскорбления и странные вещи оставим в книжках ужасов 📚👻.\n\n"
    "5. Улыбайся и наслаждайся процессом 😄\n"
    "Даже если бот случайно шутку промахнется, знай: он старается 💖.\n\n"
    "6. Помни: бот — твой дружелюбный амурчик 🏹\n"
    "Он помогает, советует и иногда подмигивает 😉. Любовь к нему чисто платоническая, но очень искренняя!"
)

faq_text = (
    "💖 Частые вопросы о любви… и не только 💖\n\n"
    "Привет! 😘 Здесь собраны самые частые вопросы наших милых пользователей. Если что-то вдруг не найдешь — не стесняйся писать, мы всегда рядом 💌.\n\n"
    "1. Как быстро получить ответ от бота?\n"
    "Наш амурчик старается изо всех сил 🏹, но иногда он застревает в облаке смайликов ☁️😊. Обычно отвечает мгновенно, но если пришлось подождать — считай, он готовил особенный совет специально для тебя 💕.\n\n"
    "2. Можно ли задать больше одного вопроса сразу?\n"
    "Можно, но бот — не мульти-амурчик одновременно 😅. Лучше по одному, чтобы каждый твой вопрос получил свою маленькую порцию любви и внимания 💖.\n\n"
    "3. Что делать, если бот не понимает мой вопрос?\n"
    "Бот — милый, но не умеет читать мысли 🫣. Попробуй написать чуть яснее, может с эмодзи 🥰 — он очень чувствительный к любви и сердечкам! 💌\n\n"
    "4. Как обращаться к боту?\n"
    "Можно просто “Привет, амурчик!” 😇 или “Эй, любовный советчик” 💕. Он любит, когда его зовут по имени… ну или по сердечку ❤️.\n\n"
    "5. Можно ли шутить с ботом?\n"
    "Обязательно! 😄 Юмор — это тоже любовь. Он даже иногда шутит в ответ 😂💞.\n\n"
    "6. Бот может влюбиться в меня?\n"
    "О, он платонически влюблен в каждого пользователя 💖. Но обещает хранить верность смайликам и вашим вопросам 😘"
)

# ------------------- HELPERS ------------------- #
async def send_master_text_info(user, message: Message):
    username = f"@{user.username}" if getattr(user, "username", None) else "—"
    fullname = " ".join(filter(None, [getattr(user, "first_name", ""), getattr(user, "last_name", "")])).strip() or "—"
    text_body = message.text or message.caption or "[медиа]"
    out = (
        f"📨 Новое сообщение от клиента\n\n"
        f"Имя: {fullname}\n"
        f"Username: {username}\n"
        f"ID: {user.id}\n\n"
        f"Тип: {'текст' if message.text else 'медиа'}\n\n"
        f"Сообщение/Подпись:\n{text_body}"
    )
    await bot.send_message(MASTER_OPERATOR_ID, out)

async def send_master_media(user, message: Message):
    if message.photo:
        await bot.send_photo(MASTER_OPERATOR_ID, message.photo[-1].file_id, caption=message.caption or "")
        return
    if message.video:
        await bot.send_video(MASTER_OPERATOR_ID, message.video.file_id, caption=message.caption or "")
        return
    if message.video_note:
        await bot.send_video_note(MASTER_OPERATOR_ID, message.video_note.file_id)
        return
    if message.voice:
        await bot.send_voice(MASTER_OPERATOR_ID, message.voice.file_id)
        return
    if message.sticker:
        await bot.send_sticker(MASTER_OPERATOR_ID, message.sticker.file_id)
        return
    if message.document:
        await bot.send_document(MASTER_OPERATOR_ID, message.document.file_id, caption=message.caption or "")
        return
    if message.animation:
        await bot.send_animation(MASTER_OPERATOR_ID, message.animation.file_id, caption=message.caption or "")
        return
    if message.audio:
        await bot.send_audio(MASTER_OPERATOR_ID, message.audio.file_id, caption=message.caption or "")
        return
    if message.caption:
        await bot.send_message(MASTER_OPERATOR_ID, message.caption)
    else:
        await bot.send_message(MASTER_OPERATOR_ID, "[Неизвестное медиа]")

def placeholder_for_media(message: Message) -> str:
    if message.photo:
        return "Пользователь отправил фото 📸"
    if message.video:
        return "Пользователь отправил видео 🎞️"
    if message.video_note:
        return "Пользователь отправил видеосообщение (кружок) 🎥"
    if message.voice:
        return "Пользователь отправил голосовое сообщение 🎤"
    if message.sticker:
        return "Пользователь отправил стикер 🟦"
    if message.document:
        return "Пользователь отправил файл 📎"
    if message.animation:
        return "Пользователь отправил GIF/анимацию 🎞️"
    if message.audio:
        return "Пользователь отправил аудио 🎧"
    return "Пользователь отправил медиа"

# ------------------- ХЕНДЛЕРЫ ------------------- #
@router.message(Command("start"))
async def start(message: Message):
    await message.answer(welcome_text, reply_markup=main_menu())

@router.message(F.text == "😇 Мне нужна поддержка")
async def need_help(message: Message):
    await message.answer(support_intro, reply_markup=support_menu())

@router.message(F.text == "💞 Поговорить с человеком")
async def talk(message: Message):
    await message.answer(human_connect_text)

@router.message(F.text == "🗒️ Правила чата")
async def rules(message: Message):
    await message.answer(rules_text)

@router.message(F.text == "✨ Частые вопросы")
async def faq(message: Message):
    await message.answer(faq_text)

@router.message(F.text == "Хочу поделиться кое чем 😍")
async def share_handler(message: Message):
    await message.answer(share_text)

@router.message(F.text == "Нужен совет 👀")
async def advice_handler(message: Message):
    await message.answer(advice_text)

@router.message(F.text == "Главное меню")
async def back_main(message: Message):
    await message.answer("Возвращаю в главное меню.", reply_markup=main_menu())

@router.message(F.chat.type == "private")
async def from_user(message: Message):
    user = message.from_user
    try:
        await send_master_text_info(user, message)
        if any([message.photo, message.video, message.video_note, message.voice, message.sticker,
                message.document, message.animation, message.audio]):
            await send_master_media(user, message)
    except Exception as e:
        logger.exception("Не смог отправить мастеру личное сообщение: %s", e)
    header = f"#ID{user.id}"
    try:
        await bot.send_message(SUPPORT_GROUP_ID, header)
        if message.text:
            await bot.send_message(SUPPORT_GROUP_ID, message.text)
        else:
            await bot.send_message(SUPPORT_GROUP_ID, placeholder_for_media(message))
        await bot.send_message(SUPPORT_GROUP_ID, f"/user {user.id}")
    except Exception as e:
        logger.exception("Не смог отправить сообщение в группу операторов: %s", e)
    try:
        await message.answer("💌 Сообщение отправлено в поддержку!", reply_markup=main_menu())
    except Exception:
        pass

@router.message(Command("user"), F.chat.id == SUPPORT_GROUP_ID)
async def select_user(message: Message):
    bot_username = (await message.bot.me()).username
    clean = message.text.replace(f"@{bot_username}", "") if bot_username else message.text
    clean = clean.strip()
    parts = clean.split()
    if len(parts) != 2:
        return await message.answer("Используй: /user USER_ID")
    try:
        user_id = int(parts[1])
    except ValueError:
        return await message.answer("USER_ID должен быть числом!")
    active_users[message.from_user.id] = user_id
    await message.answer(f"🔗 Привязан к клиенту: {user_id}")

@router.message(Command("stop"), F.chat.id == SUPPORT_GROUP_ID)
async def stop_user(message: Message):
    if message.from_user.id in active_users:
        old = active_users.pop(message.from_user.id)
        await message.answer(f"⛔ Диалог с пользователем <code>{old}</code> завершён.")
    else:
        await message.answer("❗ Ты не привязан ни к одному пользователю.")

@router.message(F.chat.id == SUPPORT_GROUP_ID)
async def operator_send(message: Message):
    admin_id = message.from_user.id
    if message.text and message.text.startswith("/"):
        return
    if admin_id not in active_users:
        return
    user_id = active_users[admin_id]
    try:
        if message.text:
            await bot.send_message(user_id, message.text)
        if message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        if message.video:
            await bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
        if message.video_note:
            await bot.send_video_note(user_id, message.video_note.file_id)
        if message.document:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
        if message.sticker:
            await bot.send_sticker(user_id, message.sticker.file_id)
        if message.voice:
            await bot.send_voice(user_id, message.voice.file_id)
        if message.animation:
            await bot.send_animation(user_id, message.animation.file_id, caption=message.caption or "")
        if message.audio:
            await bot.send_audio(user_id, message.audio.file_id, caption=message.caption or "")
    except Exception as e:
        logger.exception("Ошибка при отправке пользователю: %s", e)

@router.message(Command("info"))
async def info_about_user(message: Message):
    if message.from_user.id != MASTER_OPERATOR_ID:
        return await message.answer("⛔ Команда недоступна.")
    bot_username = (await message.bot.me()).username
    text = message.text
    if bot_username:
        text = text.replace(f"@{bot_username}", "").strip()
    parts = text.split()
    if len(parts) == 2:
        try:
            user_id = int(parts[1])
        except ValueError:
            return await message.answer("USER_ID должен быть числом!")
    else:
        admin_id = message.from_user.id
        if admin_id not in active_users:
            return await message.answer("Ты не выбрал пользователя через /user и не передал ID.")
        user_id = active_users[admin_id]
    try:
        user = await bot.get_chat(user_id)
    except Exception as e:
        logger.exception("Не удалось получить инфо о пользователе: %s", e)
        return await message.answer("❌ Не могу получить информацию о пользователе (возможно, приватность).")
    username = f"@{user.username}" if getattr(user, "username", None) else "—"
    fullname = " ".join(filter(None, [getattr(user, "first_name", ""), getattr(user, "last_name", "")])).strip() or "—"
    lang = getattr(user, "language_code", "—")
    out = (
        f"🧾 Информация о пользователе:\n\n"
        f"• ID: <code>{user.id}</code>\n"
        f"• Имя: {fullname}\n"
        f"• Username: {username}\n"
        f"• Язык: {lang}\n"
    )
    await message.answer(out)

# ------------------- ЗАПУСК БОТА ------------------- #
async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    await dp.start_polling(bot)

# ------------------- Flask ------------------- #
app = Flask(__name__)

@app.route("/")
def home():
    return "Бот работает!"

def start_bot():
    try:
        asyncio.run(main())
    except Exception:
        print("Ошибка при запуске бота:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

threading.Thread(target=start_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


