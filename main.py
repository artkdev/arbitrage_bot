import os
import time
import asyncio
from dotenv import load_dotenv
from telegram_bot import send_alert_with_button, telegram_app
from monitor import check_arbitrage_once
from aiohttp import web

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

load_dotenv()

async def main():
    print("🤖 Arbitrage bot started (Binance = read-only, Bybit = trading)...")

    asyncio.create_task(telegram_app())
    asyncio.create_task(start_web_server())

    while True:
        opportunity = check_arbitrage_once()
        if opportunity:
            message, data = opportunity
            send_alert_with_button(message, data)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
