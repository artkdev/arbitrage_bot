# Заглушка для теста — реальную торговлю добавим позже
def execute_trade(data):
    side = data["side"]
    symbol = data["symbol"]
    if side == "buy_binance_sell_bybit":
        print(f"🔁 Выставляю ордер: BUY на Binance (имитация)")
        print(f"🔁 Выставляю ордер: SELL на Bybit (имитация)")
    elif side == "buy_bybit_sell_binance":
        print(f"🔁 Выставляю ордер: BUY на Bybit (имитация)")
        print(f"🔁 Выставляю ордер: SELL на Binance (имитация)")
    else:
        print("⚠️ Неизвестное направление сделки")