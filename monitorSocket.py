import ccxt.async_support as ccxt
from dotenv import load_dotenv
import os
from telegram_bot import send_alert_with_button

load_dotenv()

PAIRS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "TON/USDT", "DOT/USDT",
    "TRX/USDT", "LINK/USDT", "AVAX/USDT", "LTC/USDT", "SHIB/USDT", "NEAR/USDT", "UNI/USDT",
    "APT/USDT", "FIL/USDT", "SAND/USDT", "LDO/USDT", "RUNE/USDT", "FLOW/USDT",
    "ID/USDT", "CYBER/USDT", "OP/USDT", "SUI/USDT", "PEPE/USDT"
]

EXCHANGES = {
    "binance": binance,
    "bybit": bybit,
    "kucoin": kucoin
}

SPREAD_THRESHOLD = 0.5  # in percent
CAPITAL = 1000

async def get_price(exchange, symbol):
    try:
        exchange_map = {
            "binance": binance,
            "bybit": bybit,
            "kucoin": kucoin
        }
        ccxt_exchange = exchange_map[exchange]
        ticker = await ccxt_exchange.watch_ticker(symbol)
        return {
            "bid": float(ticker["bid"]),
            "ask": float(ticker["ask"])
        }
    except Exception as e:
        print(f"WebSocket Error on {exchange} {symbol}: {e}")
        return None

async def check_arbitrage_all():
    all_opportunities = []

    for pair in PAIRS:
        prices = {}
        for name in EXCHANGES:
            prices[name] = await get_price(name, pair)

        for buy in EXCHANGES:
            for sell in EXCHANGES:
                if buy == sell or not prices[buy] or not prices[sell]:
                    continue

                price_buy = prices[buy]["ask"]
                price_sell = prices[sell]["bid"]
                spread = (price_sell - price_buy) / price_buy * 100

                gross = (CAPITAL / 2) * spread / 100
                fee = CAPITAL * get_fee_percent(buy, sell) / 100
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
        "kucoin": 0.08
    }
    return exchange_fees[buy] + exchange_fees[sell]