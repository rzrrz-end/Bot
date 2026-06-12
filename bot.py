import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

BOT_TOKEN = "ВАШ_ТОКЕН"
ADMIN_CHAT_ID = ID_ЧАТА_АДМИНА_ИЛИ_КАНАЛА  # например, -1001234567890 для канала

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База для хранения обращений (необязательно, но для солидности)
conn = sqlite3.connect("feedback.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    message TEXT,
    file_id TEXT,
    created_at TIMESTAMP
)
""")
conn.commit()

@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "Привет! Этот бот для обратной связи.\n"
        "Напишите ваш вопрос, пожелание или проблему. Можете приложить фото или файл.\n"
        "Администратор рассмотрит и свяжется с вами (если оставили контакт)."
    )

@dp.message(lambda msg: True)  # Обработка любых сообщений (текст, фото, документ)
async def handle_feedback(message: Message):
    user = message.from_user
    text = message.text or message.caption or "Файл без текста"
    file_id = None
    file_type = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    
    # Сохраняем в базу
    cursor.execute(
        "INSERT INTO feedback (user_id, username, message, file_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (user.id, user.username or user.first_name, text, file_id, datetime.now())
    )
    conn.commit()
    
    # Пересылаем админу
    caption = f"📩 Новое обращение\nОт: @{user.username} (ID: {user.id})\nТекст: {text}\nДата: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if file_id:
        if file_type == "photo":
            await bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=file_id, caption=caption)
        elif file_type == "document":
            await bot.send_document(chat_id=ADMIN_CHAT_ID, document=file_id, caption=caption)
    else:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=caption)
    
    # Ответ пользователю
    await message.answer("✅ Спасибо! Ваше обращение принято.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
