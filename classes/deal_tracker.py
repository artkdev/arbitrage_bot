import csv
import datetime


class DealTracker:
    def __init__(self):
        self.deals = {}
        self.csv_file = "deals.csv"
        self._init_csv()

    def _init_csv(self):
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "timestamp", "pair", "buy_exchange", "sell_exchange",
                "buy_price", "sell_price", "entry_amount", "hedge_amount",
                "status"
            ])

    def has_active(self, pair):
        return pair in self.deals

    def add(self, pair, deal):
        self.deals[pair] = deal
        self._log_deal(pair, deal, stage="entry")

    def update_hedge(self, pair, hedge_amount):
        if pair in self.deals:
            self.deals[pair]["hedge_amount"] = hedge_amount
            self._log_deal(pair, self.deals[pair], stage="hedge")

    def close(self, pair):
        self.deals.pop(pair, None)

    def _log_deal(self, pair, deal, stage="entry"):
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                deal.get("timestamp", datetime.now()),
                pair,
                deal.get("buy_exchange"),
                deal.get("sell_exchange"),
                deal.get("buy_price"),
                deal.get("sell_price"),
                deal.get("entry_amount" if stage == "entry" else None),
                deal.get("hedge_amount" if stage == "hedge" else None),
                deal.get("status")
            ])
