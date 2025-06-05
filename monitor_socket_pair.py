import ccxt.pro as ccxt
from dotenv import load_dotenv
import os
import asyncio
from telegram_bot import send_alert_with_button
from collections import defaultdict

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
    "BTC/USDT", "ETH/USDT", "BNB/USDT",
    # "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "TON/USDT", "DOT/USDT",
    # "TRX/USDT", "LINK/USDT", "AVAX/USDT", "LTC/USDT", "SHIB/USDT", "NEAR/USDT", "UNI/USDT",
    #"APT/USDT", "FIL/USDT", "SAND/USDT", 
    "LDO/USDT", 
    #"RUNE/USDT", "FLOW/USDT",
    "ID/USDT",
    "CYBER/USDT", 
    #"OP/USDT", "SUI/USDT", "PEPE/USDT"
]

EXCHANGES = {
    "binance": binance,
    "bybit": bybit,
    "kucoin": kucoin
}

# Хранилище цен: prices[exchange_id][symbol] = {bid, ask}
prices = defaultdict(dict)

CAPITAL = 1000
SPREAD_THRESHOLD = 0.5
last_opportunities = {}

def get_fee_percent(buy, sell):
    exchange_fees = {
        "binance": 0.075,
        "bybit": 0.1,
        "kucoin": 0.08
    }
    return exchange_fees[buy] + exchange_fees[sell]

async def monitor_pair(exchange, symbol):
    print(f"▶️ Старт {exchange.id.upper()} {symbol}")
    while True:
        try:
            if exchange.id == "bybit":
                order_book = await exchange.watch_order_book(symbol)
                bid = order_book['bids'][0][0] if order_book['bids'] else None
                ask = order_book['asks'][0][0] if order_book['asks'] else None
            else:
                ticker = await exchange.watch_ticker(symbol)
                bid, ask = ticker.get("bid"), ticker.get("ask")
            if bid is not None and ask is not None:
                prices[exchange.id][symbol] = {"bid": bid, "ask": ask}
                # print(f"📡 {exchange.id.upper()} {symbol} => bid: {bid}, ask: {ask}")
        except Exception as e:
            print(f"❌ WebSocket error {exchange.id} {symbol}: {e}")
            await asyncio.sleep(1)

async def check_arbitrage_loop():
    while True:
        await asyncio.sleep(2)
        for pair in PAIRS:
            try:
                exchange_data = {name: prices[name].get(pair) for name in EXCHANGES}
                if any(v is None for v in exchange_data.values()):
                    continue

                for buy_name in EXCHANGES:
                    for sell_name in EXCHANGES:
                        if buy_name == sell_name:
                            continue

                        buy = exchange_data[buy_name]
                        sell = exchange_data[sell_name]

                        spread = (sell['bid'] - buy['ask']) / buy['ask'] * 100
                        if spread > 0.4:
                            key = f"{pair}:{buy_name}->{sell_name}"
                            value = (buy['ask'], sell['bid'])
                            if last_opportunities.get(key) == value:
                                continue
                            last_opportunities[key] = value

                            gross, fee, net = log_opportunity(pair, buy_name, buy['ask'], sell_name, sell['bid'],
                                                              spread)

                            await send_alert_with_button(
                                f"💱 Арбитраж {pair}\n\n"
                                f"🔻 Купил на {buy_name} за {buy['ask']:.6f}\n"
                                f"🔺 Продал на {sell_name} за {sell['bid']:.6f}\n\n"
                                f"📊 Спред: {spread:.2f}%\n"
                                f"💰 Валовая прибыль: ${gross:.2f}\n"
                                f"💸 Комиссия: ${fee:.2f}\n"
                                f"{'✅ Чистая прибыль' if net > 0 else '❌ Убыток'}: ${net:.2f}",
                                {
                                    "side": "arbitrage",
                                    "symbol": pair,
                                    "binance_price": prices["binance"].get(pair, {}).get("bid"),
                                    "bybit_price": prices["bybit"].get(pair, {}).get("ask")
                                }
                            )
            except Exception as e:
                print(f"⚠️ Ошибка в расчёте арбитража: {e}")


def log_opportunity(pair, buy_name, buy_price, sell_name, sell_price, spread):
    working_capital = CAPITAL / 2
    gross = working_capital * spread / 100
    fee_percent = get_fee_percent(buy_name, sell_name)
    fee = CAPITAL * fee_percent / 100
    net = gross - fee
    gap = SPREAD_THRESHOLD - spread

    print(f"\n=== Арбитраж по {pair} ===")
    print(f"🔻 Купи на {buy_name} за {buy_price:.6f}")
    print(f"🔺 Продай на {sell_name} за {sell_price:.6f}")
    print(f"📊 Спред: {spread:.2f}%")
    print(f"💰 Валовая прибыль: ${gross:.2f}")
    print(f"💸 Комиссия: ${fee:.2f}")
    print(f"{'✅ Чистая прибыль' if net > 0 else '❌ Убыток'}: ${net:.2f}")
    if gap > 0:
        print(f"⏳ До порога {SPREAD_THRESHOLD}% не хватает: {gap:.2f}%")
    return gross, fee, net