import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import API_TOKEN
from database import init_db, save_record, get_history

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

med_schedule = {
    "08:10": ["Магне Б6 форте", "Тримекор MR 35мг", "Ибупрофен 200мг", "Вольфуран"],
    "12:50": ["Барол 20мг"],
    "13:10": ["Тримедат форте"],
    "13:40": ["Магне Б6 форте", "Тримекор MR 35мг", "Ибупрофен 200мг", "Вольфуран"],
    "19:40": ["Тримедат форте"],
    "20:10": ["Магне Б6 форте", "Тримекор MR 35мг", "Ибупрофен 200мг"],
}

user_id_storage = {}

confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Принял"),
            KeyboardButton(text="❌ Пропустил")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id

    schedule_text = "<b>📅 Расписание приёма лекарств</b>\n\n"
    for time, meds in med_schedule.items():
        meds_list = "\n".join(f"▫️ <i>{med}</i>" for med in meds)
        schedule_text += f"<b>{time}</b>:\n{meds_list}\n\n"

    await message.answer(
        "Привет! Я буду напоминать тебе о приёме лекарств по расписанию.\n"
        "Используй /history чтобы посмотреть историю.\n\n" +
        schedule_text,
        parse_mode="HTML"
    )
    schedule_reminders(user_id)
    logging.info(f"Started reminders for user {user_id}")



@dp.message(Command("history"))
async def history_command(message: types.Message):
    user_id = message.from_user.id
    records = await get_history(user_id)
    if not records:
        await message.answer("История пуста.")
        return
    text = "📋 Последние приёмы:\n"
    for med, time_str, status, ts in records:
        text += f"{ts[:16]} — {med} в {time_str} — {status}\n"
    await message.answer(text)

@dp.message()
async def confirm_handler(message: types.Message):
    if message.text not in ["✅ Принял", "❌ Пропустил"]:
        return
    user_id = message.from_user.id
    time_meds = user_id_storage.get(user_id)
    if not time_meds:
        await message.answer("Нет активного напоминания.")
        return
    time_str, meds = time_meds
    status = "принято" if message.text == "✅ Принял" else "пропущено"
    for med in meds:
        await save_record(user_id, med, time_str, status)
    await message.answer("Записал! ✅")
    logging.info(f"Recorded {status} for user {user_id} at {time_str}")

async def send_reminder(time_str: str, user_id: int):
    meds = med_schedule.get(time_str, [])
    if meds:
        user_id_storage[user_id] = (time_str, meds)
        msg = f"🕗 {time_str} — Пора принять:\n" + "\n".join(f"• {m}" for m in meds)
        await bot.send_message(user_id, msg, reply_markup=confirm_keyboard)
        logging.info(f"Sent reminder to user {user_id} at {time_str}")

def schedule_reminders(user_id: int):
    for time_str in med_schedule:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(send_reminder, 'cron', hour=hour, minute=minute, args=[time_str, user_id])
    logging.info(f"Scheduled reminders for user {user_id}")

async def main():
    await init_db()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
