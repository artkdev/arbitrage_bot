      
import asyncio
import datetime
from monitor_socket_pair import CAPITAL, EXCHANGES


class DealTracker:
    def __init__(self):
        self.deals = {}

    def has_active(self, pair):
        return pair in self.deals

    def add(self, pair, deal):
        self.deals[pair] = deal

    def close(self, pair):
        self.deals.pop(pair, None)

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
            print(f"❌ Сделка не исполнена — отмена")
            
class Rebalancer:
    def __init__(self, tracker, prices):
        self.tracker = tracker
        self.prices = prices

    async def check(self):
        for pair, deal in list(self.tracker.deals.items()):
            buy_ex = deal['buy_exchange']
            sell_ex = deal['sell_exchange']
            current_bid = self.prices[buy_ex].get(pair, {}).get("bid")
            current_ask = self.prices[sell_ex].get(pair, {}).get("ask")

            if current_bid and current_ask and abs(current_bid - current_ask) / current_bid < 0.2 / 100:
                print(f"🔁 Выровнено по {pair} — выполнение обратной сделки (хедж)")

                amount = CAPITAL / 2 / deal['buy_price']
                exchange_buy = EXCHANGES[deal['sell_exchange']]
                exchange_sell = EXCHANGES[deal['buy_exchange']]

                try:
                    await exchange_sell.create_limit_sell_order(pair, amount, current_bid)
                    await exchange_buy.create_limit_buy_order(pair, amount, current_ask)
                    print(f"✅ Хедж-ордера отправлены по {pair}")
                except Exception as e:
                    print(f"❌ Ошибка при отправке хедж-ордеров по {pair}: {e}")

                self.tracker.close(pair)
