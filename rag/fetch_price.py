import yfinance as yf

class FetchPrice:
    def __init__(self,ticker):
        self.ticker=ticker

    def fetch_price(self):
        try:
            stock=yf.Ticker(self.ticker)
            data=stock.history(period="1d",interval="1m")
            if not data.empty:
                current_price=data['Close'].iloc[-1]
                return float(current_price)
            else:
                return None
        except Exception as e:
            print(f"Error fetching price for {self.ticker}: {e}")
            return None
        