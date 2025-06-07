import asyncio
import datetime

from monitor_socket_pair import CAPITAL, EXCHANGES

class TradeExecutor:
    def __init__(self, tracker):
        self.tracker = tracker

    async def execute(self, pair, buy_name, sell_name, buy_price, sell_price):
        if self.tracker.has_active(pair):
            return

        print(f"🚀 Исполнение ордеров на {buy_name} и {sell_name} для {pair}")
        exchange_buy = EXCHANGES[buy_name]
        exchange_sell = EXCHANGES[sell_name]
        amount = CAPITAL / 2 / buy_price

        buy_task = asyncio.create_task(exchange_buy.create_limit_buy_order(pair, amount, buy_price))
        sell_task = asyncio.create_task(exchange_sell.create_limit_sell_order(pair, amount, sell_price))

        done, pending = await asyncio.wait([buy_task, sell_task], timeout=10)

        for task in pending:
            task.cancel()

        executed = any(task in done for task in [buy_task, sell_task])

        if executed:
            self.tracker.add(pair, {
                "buy_exchange": buy_name,
                "sell_exchange": sell_name,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "status": "open",
                "timestamp": datetime.now()
            })
            print(f"✅ Сделка открыта по {pair}")
        else:
            print("❌ Сделка не исполнена — отмена")