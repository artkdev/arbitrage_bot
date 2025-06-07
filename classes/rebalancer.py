from monitor_socket_pair import CAPITAL, EXCHANGES


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