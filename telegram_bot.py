import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv
from trading import execute_trade

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

pending_actions = {}

def send_alert_with_button(message: str, data: dict):
    callback_data = f"approve:{data['side']}:{data['symbol']}"
    pending_actions[callback_data] = data

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить сделку", callback_data=callback_data)]
    ])

    asyncio.create_task(bot.send_message(chat_id=TELEGRAM_USER_ID, text=message, reply_markup=markup))

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