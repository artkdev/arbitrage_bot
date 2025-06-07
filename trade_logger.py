from datetime import datetime

def log_trade_to_file(pair, buy_name, buy_price, sell_name, sell_price, spread, gross, fee, net, status):
    with open("trade_history.log", "a") as f:
        f.write(f"{datetime.now().isoformat()} | {pair} | BUY {buy_name} @ {buy_price} | "
                f"SELL {sell_name} @ {sell_price} | Spread: {spread:.2f}% | "
                f"Gross: ${gross:.2f} | Fee: ${fee:.2f} | Net: ${net:.2f} | Status: {status}\n")
