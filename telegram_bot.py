import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from trading import execute_trade
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

pending_actions = {}

@dp.message(Command("ping"))
async def ping_command(message: Message):
    await message.answer("✅ Бот в сети!")

async def send_alert_with_button(message, data):
    if data.get("side") == "log":
        await bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить сделку",
                    callback_data=f"approve:{data['side']}:{data['symbol']}"
                )
            ]
        ]
    )

    await bot.send_message(chat_id=TELEGRAM_USER_ID, text=message, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("approve:"))
async def process_callback(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    callback_data = callback.data
    data = pending_actions.get(callback_data)
    if data:
        await bot.send_message(chat_id=TELEGRAM_USER_ID, text=f"✅ Сделка подтверждена: {data['side']}")
        execute_trade(data)
        print(f"CONFIRMED: {data}")
        pending_actions.pop(callback_data)

async def telegram_app():
    await dp.start_polling(bot)