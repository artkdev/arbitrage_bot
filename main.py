import asyncio
from dotenv import load_dotenv
from monitor_socket_pair import monitor_pair, check_arbitrage_loop, EXCHANGES, PAIRS
from aiohttp import web

from telegram_bot import telegram_app, send_alert_with_button

load_dotenv()

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
    print("🤖 Arbitrage bot started (WebSockets for each pair/exchange)...")

    asyncio.create_task(telegram_app())
    asyncio.create_task(start_web_server())

    await asyncio.sleep(1)

    await send_alert_with_button("✅ Bot run successfully", {
        "side": "test",
        "symbol": "TEST/USDT",
        "binance_price": 0,
        "bybit_price": 0
    })

    tasks = []

    for ex in EXCHANGES.values():
        for pair in PAIRS:
            tasks.append(asyncio.create_task(monitor_pair(ex, pair)))

    tasks.append(asyncio.create_task(check_arbitrage_loop()))

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())