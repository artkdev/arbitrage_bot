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
TELEGRAM_USER_IDS = [int(x) for x in os.getenv("TELEGRAM_USER_IDS").split(",")]

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

pending_actions = {}

@dp.message(Command("ping"))
async def ping_command(message: Message):
    await message.answer("✅ Бот в сети!")

async def send_alert_with_button(message, data):
    print("message", message)
    print("data", data)

    symbol = data.get("symbol")

    # 🛡️ Безопасность: если символ — список, берём первый
    if isinstance(symbol, list):
        symbol = symbol[0]

    # 🛡️ Безопасный callback_data (Telegram максимум 64 символа)
    callback_data = f"approve:{data.get('side')}:{symbol}"
    if len(callback_data) > 64:
        callback_data = callback_data[:60] + "..."

    # 🟢 Если это просто лог — без кнопки
    if data.get("side") == "log":
        for user_id in TELEGRAM_USER_IDS:
            await bot.send_message(chat_id=user_id, text=message)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить сделку",
                    callback_data=callback_data
                )
            ]
        ]
    )

    for user_id in TELEGRAM_USER_IDS:
        await bot.send_message(chat_id=user_id, text=message, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("approve:"))
async def process_callback(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    callback_data = callback.data
    data = pending_actions.get(callback_data)
    if data:
        for user_id in TELEGRAM_USER_IDS:
            await bot.send_message(chat_id=user_id, text=f"✅ Сделка подтверждена: {data['side']}")
        execute_trade(data)
        print(f"CONFIRMED: {data}")
        pending_actions.pop(callback_data)

async def telegram_app():
    await dp.start_polling(bot)