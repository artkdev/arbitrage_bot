import os
import time
import asyncio
from dotenv import load_dotenv
from telegram_bot import send_alert_with_button, telegram_app
from monitorSocket import check_arbitrage_all
from aiohttp import web

load_dotenv()
PROXY_URL = os.getenv("PROXY_URL")

# HTTP handler для Render
async def handle(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def main():
    print("🤖 Arbitrage bot started (Binance = read-only, Bybit = trading)...")
    if PROXY_URL:
        print(f"🌐 Используется прокси: {PROXY_URL}")
    else:
        print("⚠️ Прокси не указан, будет прямое подключение.")

    asyncio.create_task(telegram_app())
    asyncio.create_task(start_web_server())

    await asyncio.sleep(1)

    await send_alert_with_button("✅ Bot run successfully", {
        "side": "test",
        "symbol": "TEST/USDT",
        "binance_price": 0,
        "bybit_price": 0
    })

    while True:
        print("🔄 Проверка арбитража...")
        try:
            opportunity = await check_arbitrage_all()
            if opportunity:
                message, data = opportunity
                await send_alert_with_button(message, data)
        except Exception as e:
            print(f"⚠️ Ошибка в check_arbitrage_once(): {e}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
