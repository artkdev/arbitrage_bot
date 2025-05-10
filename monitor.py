import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

binance = ccxt.binance({
    'apiKey': os.getenv("BINANCE_API_KEY"),
    'secret': os.getenv("BINANCE_API_SECRET"),
})

bybit = ccxt.bybit({
    'apiKey': os.getenv("BYBIT_API_KEY"),
    'secret': os.getenv("BYBIT_API_SECRET"),
})

PAIR = "ID/USDT"
SPREAD_THRESHOLD = 0.5  # in percent
CAPITAL = 1000
FEE_BINANCE = 0.075
FEE_BYBIT = 0.1

def get_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"Ошибка получения цены с {exchange.id}: {e}")
        return None

def check_arbitrage_once():
    binance_price = get_price(binance, PAIR)
    bybit_price = get_price(bybit, PAIR)

    if not binance_price or not bybit_price:
        return None

    spread_binance_to_bybit = (bybit_price - binance_price) / binance_price * 100
    spread_bybit_to_binance = (binance_price - bybit_price) / bybit_price * 100

    print(
        f"Пара: {PAIR}\n"
        f"Binance: {binance_price:.6f} (комиссия {FEE_BINANCE}%)\n"
        f"Bybit: {bybit_price:.6f} (комиссия {FEE_BYBIT}%)"
    )

    if bybit_price > binance_price and spread_binance_to_bybit >= SPREAD_THRESHOLD:
        gross = (CAPITAL * spread_binance_to_bybit) / 100 / 2
        fee = CAPITAL * (FEE_BINANCE + FEE_BYBIT) / 100
        net = gross - fee
        print(
            f"\n📊 Лучший спред: {spread_binance_to_bybit:.2f}% между Binance и Bybit\n"
            f"💰 Прибыль ДО комиссии: ${gross:.2f}\n"
            f"💸 Комиссия: ${fee:.2f}\n"
            f"✅ Чистая прибыль: ${net:.2f}\n"
            f"💡 Выгодно: покупай на Binance, продавай на Bybit"
        )
        message = (
            f"Пара: {PAIR} "
            f"Binance: {binance_price:.6f} (комиссия {FEE_BINANCE}%) "
            f"Bybit: {bybit_price:.6f} (комиссия {FEE_BYBIT}%) "
            f" 📊 Спред: {spread_binance_to_bybit:.2f}% "
            f"💰 До комиссии: ${gross:.2f} "
            f"💸 Комиссия: ${fee:.2f} "
            f"✅ Чистая прибыль: ${net:.2f}"
        )
        data = {
            "side": "buy_binance_sell_bybit",
            "symbol": PAIR,
            "binance_price": binance_price,
            "bybit_price": bybit_price
        }
        return message, data

    elif binance_price > bybit_price and spread_bybit_to_binance >= SPREAD_THRESHOLD:
        gross = (CAPITAL * spread_bybit_to_binance) / 100 / 2
        fee = CAPITAL * (FEE_BINANCE + FEE_BYBIT) / 100
        net = gross - fee
        print(
            f"\n📊 Лучший спред: {spread_bybit_to_binance:.2f}% между Bybit и Binance\n"
            f"💰 Прибыль ДО комиссии: ${gross:.2f}\n"
            f"💸 Комиссия: ${fee:.2f}\n"
            f"✅ Чистая прибыль: ${net:.2f}\n"
            f"💡 Выгодно: покупай на Bybit, продавай на Binance"
        )
        message = (
            f"Пара: {PAIR} "
            f"Binance: {binance_price:.6f} (комиссия {FEE_BINANCE}%) "
            f"Bybit: {bybit_price:.6f} (комиссия {FEE_BYBIT}%) "
            f" 📊 Спред: {spread_bybit_to_binance:.2f}% "
            f"💰 До комиссии: ${gross:.2f} "
            f"💸 Комиссия: ${fee:.2f} "
            f"✅ Чистая прибыль: ${net:.2f}"
        )
        data = {
            "side": "buy_bybit_sell_binance",
            "symbol": PAIR,
            "binance_price": binance_price,
            "bybit_price": bybit_price
        }
        return message, data

    print(f"\nℹ️ Нет подходящего спреда: всего {max(spread_binance_to_bybit, spread_bybit_to_binance):.2f}% — ниже порога {SPREAD_THRESHOLD}%")
    return None
