import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

from database import create_tables, add_user, update_score, get_score, get_top_users

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM для регистрации
class Registration(StatesGroup):
    full_name = State()
    phone = State()
    email = State()

# Вопросы для теста
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

user_answers = {}

# /start — начало и регистрация
@dp.message(F.text == "/start")
async def handle_start(message: Message, state: FSMContext):
    await message.answer("👋 Добро пожаловать! Давайте зарегистрируемся.\nВведите ваше ФИО:")
    await state.set_state(Registration.full_name)

@dp.message(Registration.full_name)
async def handle_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("📞 Поделитесь номером телефона:", reply_markup=keyboard)
    await state.set_state(Registration.phone)

@dp.message(Registration.phone, F.contact)
async def handle_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("📧 Введите ваш Email:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.email)

@dp.message(Registration.email)
async def handle_email(message: Message, state: FSMContext):
    data = await state.update_data(email=message.text)
    user_data = await state.get_data()
    add_user(
        telegram_id=message.from_user.id,
        full_name=user_data["full_name"],
        phone=user_data["phone"],
        email=user_data["email"]
    )
    await message.answer("✅ Регистрация завершена! Используйте /test чтобы пройти тест или /points чтобы узнать баллы.")
    await state.clear()

# /test — начало теста
@dp.message(F.text == "/test")
async def start_test(message: Message):
    user_id = message.from_user.id
    user_answers[user_id] = {"score": 0, "current": 0}
    await send_question(message.chat.id, user_id)

@dp.message(F.text == "/myid")
async def show_my_id(message: Message):
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")

# /points — баллы
@dp.message(F.text == "/points")
async def show_points(message: Message):
    score = get_score(message.from_user.id)
    await message.answer(f"🌟 Ваши баллы: {score}")

MY_ADMIN_ID = 1631928667  # <-- Замени на свой настоящий ID

@dp.message(F.text == "/export_users")
async def export_users(message: Message):
    if message.from_user.id != MY_ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды.")
        return

    from database import get_all_users
    import csv

    users = get_all_users()

    if not users:
        await message.answer("Пользователи не найдены.")
        return

    file_path = "users_export.csv"

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ФИО", "Телефон", "Email", "Баллы"])
        writer.writerows(users)

    await message.answer_document(types.FSInputFile(file_path), caption="📄 Список пользователей")

# /top — топ-лидеры
@dp.message(F.text == "/top")
async def show_top(message: Message):
    top_users = get_top_users()
    text = "🏆 ТОП-5 участников:\n\n"
    for i, (name, score) in enumerate(top_users, 1):
        text += f"{i}. {name} — {score} баллов\n"
    await message.answer(text)

# Отправка вопроса
async def send_question(chat_id, user_id):
    current = user_answers[user_id]["current"]
    if current >= len(questions):
        score = user_answers[user_id]["score"]
        update_score(user_id, score)
        await bot.send_message(chat_id, f"✅ Тест завершён! Вы набрали {score} из {len(questions)} баллов.")
        return

    q = questions[current]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"answer_{i}")]
            for i, opt in enumerate(q["options"])
        ]
    )
    await bot.send_message(chat_id, q["question"], reply_markup=keyboard)

# Обработка ответов
@dp.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    current = user_answers[user_id]["current"]
    correct_index = questions[current]["correct"]
    selected = int(callback.data.split("_")[1])

    if selected == correct_index:
        user_answers[user_id]["score"] += 1
        await callback.answer("✅ Верно!")
    else:
        await callback.answer("❌ Неверно.")

    user_answers[user_id]["current"] += 1
    await send_question(callback.message.chat.id, user_id)

# Запуск
async def main():
    create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
