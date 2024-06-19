import yfinance as yf
import pandas as pd


class StockAPI:
    def __init__(self):
        pass

    def get_stock_price(self, symbol: str) -> float:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            return None

    def get_stock_history(self, symbol, interval: str) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='max', interval=interval)
        return data.reset_index()  # Reset index to convert to pandas DataFrame

        
