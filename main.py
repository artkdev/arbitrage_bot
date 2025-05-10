import os
import time
import asyncio
from dotenv import load_dotenv
from telegram_bot import send_alert_with_button, telegram_app
from monitor import check_arbitrage_once

# Загрузка переменных окружения
load_dotenv()

async def main():
    print("🤖 Arbitrage bot started (Binance = read-only, Bybit = trading)...")
    # Запускаем Telegram-бота параллельно
    asyncio.create_task(telegram_app())

    while True:
        opportunity = check_arbitrage_once()
        if opportunity:
            message, data = opportunity
            send_alert_with_button(message, data)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
