import ccxt.pro as ccxt
from dotenv import load_dotenv
import os
import asyncio
from telegram_bot import send_alert_with_button

load_dotenv()

binance = ccxt.binance({
    'apiKey': os.getenv("BINANCE_API_KEY"),
    'secret': os.getenv("BINANCE_API_SECRET"),
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

bybit = ccxt.bybit({
    'apiKey': os.getenv("BYBIT_API_KEY"),
    'secret': os.getenv("BYBIT_API_SECRET"),
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

kucoin = ccxt.kucoin({
    'apiKey': os.getenv("KUCOIN_API_KEY"),
    'secret': os.getenv("KUCOIN_API_SECRET"),
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

PAIRS = [
    #"BTC/USDT", "ETH/USDT", "BNB/USDT",
    # "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "TON/USDT", "DOT/USDT",
    # "TRX/USDT", "LINK/USDT", "AVAX/USDT", "LTC/USDT", "SHIB/USDT", "NEAR/USDT", "UNI/USDT",
    #"APT/USDT", "FIL/USDT", "SAND/USDT", 
    "LDO/USDT", 
    #"RUNE/USDT", "FLOW/USDT",
    #"ID/USDT", 
    "CYBER/USDT", 
    #"OP/USDT", "SUI/USDT", "PEPE/USDT"
]

EXCHANGES = {
    "binance": binance,
    #"bybit": bybit,
    "kucoin": kucoin
}

SPREAD_THRESHOLD = 0.5  # in percent
CAPITAL = 1000

async def get_price(exchange, symbol, retries=3, delay=0.5):
    exchange_map = {
        "binance": binance,
        #"bybit": bybit,
        "kucoin": kucoin
    }
    ccxt_exchange = exchange_map[exchange]

    for attempt in range(retries):
        try:
            ticker = await ccxt_exchange.watch_ticker(symbol)
            bid = ticker.get("bid")
            ask = ticker.get("ask")

            if bid is None or ask is None:
                raise ValueError("Bid or Ask is None")

            return {
                "bid": float(bid),
                "ask": float(ask)
            }

        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                print(f"❌ WebSocket Error on {exchange} {symbol}: {e}")
                return None

async def check_arbitrage_for_pair(pair):
    print(f"\n🔍 Проверка арбитража для {pair}")
    prices = {}

    tasks = [get_price(name, pair) for name in EXCHANGES]
    results = await asyncio.gather(*tasks)

    for idx, name in enumerate(EXCHANGES):
        price = results[idx]
        if not price:
            return
        prices[name] = price
        print(f"📡 {pair} {name} => {price}")

    for buy in EXCHANGES:
        for sell in EXCHANGES:
            if buy == sell:
                continue
            price_buy = prices[buy]["ask"]
            price_sell = prices[sell]["bid"]
            spread = (price_sell - price_buy) / price_buy * 100

            gross = (CAPITAL / 2) * spread / 100
            fee = CAPITAL * get_fee_percent(buy, sell) / 100
            net = gross - fee

            await log_opportunity(
                pair=pair,
                exchange_buy=buy,
                price_buy=price_buy,
                exchange_sell=sell,
                price_sell=price_sell,
                spread=spread,
                threshold=SPREAD_THRESHOLD,
                capital=CAPITAL,
                is_alert=(spread >= SPREAD_THRESHOLD or spread > 0.25)
            )

async def check_arbitrage_all():
    print("✅ check_arbitrage_all from monitorSocket is running")
    for pair in PAIRS:
        await check_arbitrage_for_pair(pair)

async def log_opportunity(pair, exchange_buy, price_buy, exchange_sell, price_sell, spread, threshold, capital, is_alert=True):
    print("start log_opportunity")
    working_capital = capital / 2
    fee_percent = get_fee_percent(exchange_buy.lower(), exchange_sell.lower())
    gross = working_capital * spread / 100
    fee = capital * fee_percent / 100
    net = gross - fee
    gap = threshold - spread

    if spread > 0:
        print(f"\n=== Арбитраж по {pair} ===")
        print(f"🔻 Купи на {exchange_buy} за {price_buy:.6f}")
        print(f"🔺 Продай на {exchange_sell} за {price_sell:.6f}")
        print(f"📊 Спред: {spread:.2f}%")
        print(f"💰 Валовая прибыль: ${gross:.2f}")
        print(f"💸 Комиссия: ${fee:.2f}")
        print(f"{'✅ Чистая прибыль' if net > 0 else '❌ Убыток'}: ${net:.2f}")
        if gap > 0:
            print(f"⏳ До порога {threshold}% не хватает: {gap:.2f}%")

    # Формат для Telegram
    if is_alert or spread > 0.3:
        message = (
            f"💱 Арбитраж {pair}\n\n"
            f"🔻 Купил на {exchange_buy} за {price_buy:.6f}\n"
            f"🔺 Продал на {exchange_sell} за {price_sell:.6f}\n\n"
            f"📊 Спред: {spread:.2f}%\n"
            f"💰 Валовая прибыль: ${gross:.2f}\n"
            f"💸 Комиссия: ${fee:.2f}\n"
            f"{'✅ Чистая прибыль' if net > 0 else '❌ Убыток'}: ${net:.2f}"
        )

        await send_alert_with_button(message, {
            "side": f"buy_{exchange_buy.lower()}_sell_{exchange_sell.lower()}",
            "symbol": pair,
            "binance_price": price_buy if exchange_buy == "Binance" else price_sell,
            "bybit_price": price_buy if exchange_buy == "Bybit" else price_sell
        })


def get_fee_percent(buy, sell):
    exchange_fees = {
        "binance": 0.075,
        "bybit": 0.1,
        "kucoin": 0.08
    }
    return exchange_fees[buy] + exchange_fees[sell]