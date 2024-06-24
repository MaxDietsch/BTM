import yfinance as yf
import pandas as pd


class StockAPI:
    def __init__(self):
        pass

    
    def check_symbol(self, symbol: str) -> str:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            if hist.empty:
                return 0 
            return 1 
        except Exception as e:
            return 0


    def get_stock_price(self, symbol: str) -> float:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            return 0

    def get_stock_history(self, symbol, interval: str = '5y') -> pd.DataFrame:
        try:
            stock = yf.Ticker(symbol)
                        
            info = stock.history(period = interval)
            info = info.reset_index().to_dict(orient='records')
            for record in info:
                if isinstance(record['Date'], pd.Timestamp):
                    record['Date'] = record['Date'].strftime('%Y-%m-%d')
            
            return info
            
        except Exception as e:
            return 0

    def format_chart_data(self, info):
        labels = [record['Date'] for record in info]
        data = [record['Close'] for record in info]

        chart_data = {
            'labels': labels,
            'datasets': [{
                'label': 'Stock Price',
                'data': data,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }]
        }
        return chart_data
        
