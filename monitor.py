import ccxt
from ccxt import kucoin
from dotenv import load_dotenv
import requests
import os
from telegram_bot import send_alert_with_button

load_dotenv()

binance = ccxt.binance({
    'apiKey': os.getenv("BINANCE_API_KEY"),
    'secret': os.getenv("BINANCE_API_SECRET"),
})

bybit = ccxt.bybit({
    'apiKey': os.getenv("BYBIT_API_KEY"),
    'secret': os.getenv("BYBIT_API_SECRET"),
})

kucoin = ccxt.kucoin({
    'apiKey': os.getenv("KUCOIN_API_KEY"),
    'secret': os.getenv("KUCOIN_API_SECRET"),
})
#, "MATICUSDT"
#, "RNDRUSDT"
#, "FTMUSDT"
PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "TONUSDT", "DOTUSDT",
    "TRXUSDT", "LINKUSDT", "AVAXUSDT", "LTCUSDT", "SHIBUSDT", "NEARUSDT", "UNIUSDT",
    "APTUSDT", "FILUSDT", "SANDUSDT", "LDOUSDT", "RUNEUSDT", "FLOWUSDT",
    "IDUSDT", "CYBERUSDT", "OPUSDT", "SUIUSDT", "PEPEUSDT"
]

EXCHANGES = ["binance", "bybit", "kucoin"]

SPREAD_THRESHOLD = 0.5  # in percent
CAPITAL = 1000
FEE_BINANCE = 0.075
FEE_BYBIT = 0.1

async def get_price(exchange, symbol):
    proxies = {}
    proxy_url = os.getenv("PROXY_URL")

    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}
    else:
        proxies = None

    try:
        if exchange == "binance":
            url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
            response = requests.get(url, proxies=proxies, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                "last": float(data["bidPrice"]),
                "bid": float(data["bidPrice"]),
                "ask": float(data["askPrice"])
            }

        elif exchange == "bybit":
            url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
            response = requests.get(url, proxies=proxies, timeout=10)
            response.raise_for_status()
            result = response.json().get("result")
            if not result or "list" not in result or not result["list"]:
                raise ValueError(f"Bybit: нет данных для {symbol}")

            data = result["list"][0]

            return {
                "last": float(data["lastPrice"]),
                "bid": float(data["bid1Price"]),
                "ask": float(data["ask1Price"])
            }

        elif exchange == "kucoin":
            symbol = symbol.replace("USDT", "-USDT")  # KuCoin формат
            url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
            res = requests.get(url, timeout=10)
            res.raise_for_status()

            json_data = res.json()
            if not json_data or not json_data.get("data"):
                raise ValueError(f"Нет данных от KuCoin для {symbol}")
            data = json_data["data"]
            return {
                "bid": float(data["bestBid"]),
                "ask": float(data["bestAsk"])
            }

        else:
            raise ValueError("Неизвестная биржа")

    except Exception as e:
        await send_alert_with_button(f"❌ Ошибка {exchange}: {e}", {
            "side": "log",
            "symbol": symbol,
            "binance_price": 0,
            "bybit_price": 0
        })
        return None

# async def check_arbitrage_once():
#     binance = await get_price("binance", PAIR)
#     bybit = await get_price("bybit", PAIR)
#
#     if not binance or not bybit:
#         return None
#
#     spread_b2b = (bybit["bid"] - binance["ask"]) / binance["ask"] * 100
#     spread_b2y = (binance["bid"] - bybit["ask"]) / bybit["ask"] * 100
#
#     if spread_b2b >= SPREAD_THRESHOLD:
#         await log_opportunity(
#             exchange_buy="Binance",
#             price_buy=binance["ask"],
#             exchange_sell="Bybit",
#             price_sell=bybit["bid"],
#             spread=spread_b2b,
#             threshold=SPREAD_THRESHOLD,
#             capital=CAPITAL,
#             is_alert=True
#         )
#         return "ok", {}
#
#     elif spread_b2y >= SPREAD_THRESHOLD:
#         await log_opportunity(
#             exchange_buy="Bybit",
#             price_buy=bybit["ask"],
#             exchange_sell="Binance",
#             price_sell=binance["bid"],
#             spread=spread_b2y,
#             threshold=SPREAD_THRESHOLD,
#             capital=CAPITAL,
#             is_alert=True
#         )
#         return "ok", {}
#
#     max_spread = max(spread_b2b, spread_b2y)
#     gap = SPREAD_THRESHOLD - max_spread
#
#     print(f"⛔ Нет сигнала. Спреды: B→B = {spread_b2b:.2f}%, B→Y = {spread_b2y:.2f}%, порог = {SPREAD_THRESHOLD}%")
#     print(f"⏳ До минимального порога не хватает: {gap:.2f}%")
#
#     return None

async def check_arbitrage_all():
    all_opportunities = []

    for pair in PAIRS:
        prices = {}
        for exchange in EXCHANGES:
            prices[exchange] = await get_price(exchange, pair)

        for buy in EXCHANGES:
            for sell in EXCHANGES:
                if buy == sell:
                    continue
                if prices[buy] is None or prices[sell] is None:
                    continue

                price_buy = prices[buy]["ask"]
                price_sell = prices[sell]["bid"]
                spread = (price_sell - price_buy) / price_buy * 100

                gross = (CAPITAL / 2) * spread / 100
                fee = CAPITAL * (FEE_BINANCE + FEE_BYBIT) / 100
                net = gross - fee

                all_opportunities.append({
                    "pair": pair,
                    "buy_exchange": buy,
                    "sell_exchange": sell,
                    "price_buy": price_buy,
                    "price_sell": price_sell,
                    "spread": spread,
                    "gross": gross,
                    "fee": fee,
                    "net": net
                })

    # ✅ Сортировка по убыванию спреда и вывод только 3 лучших
    top_opportunities = sorted(all_opportunities, key=lambda x: x["spread"], reverse=True)[:3]

    for opp in top_opportunities:
        await log_opportunity(
            pair=opp["pair"],
            exchange_buy=opp["buy_exchange"],
            price_buy=opp["price_buy"],
            exchange_sell=opp["sell_exchange"],
            price_sell=opp["price_sell"],
            spread=opp["spread"],
            threshold=SPREAD_THRESHOLD,
            capital=CAPITAL,
            is_alert=(opp["spread"] >= SPREAD_THRESHOLD or opp["spread"] > 0.25)
        )



async def log_opportunity(pair, exchange_buy, price_buy, exchange_sell, price_sell, spread, threshold, capital, is_alert=False):
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
        "kucoin": 0.1
    }
    return exchange_fees[buy] + exchange_fees[sell]