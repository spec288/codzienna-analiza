import pandas as pd
import numpy as np
import requests
import logging
from tradingview_ta import TA_Handler, Interval
from datetime import datetime

# Konfiguracja
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"
CHAT_ID = "-1002655090041"
SYMBOLS = {
    "US30 (Dow Jones)": "US30USD",
    "DAX (Germany 40)": "GER40"
}
INTERVAL = Interval.INTERVAL_5_MINUTES

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trend_analysis.log'),
        logging.StreamHandler()
    ]
)

class TradingViewAnalyzer:
    def __init__(self, symbol, ticker):
        self.symbol = symbol
        self.ticker = ticker
        self.handler = TA_Handler(
            symbol=ticker,
            screener="cfd",
            exchange="FOREXCOM",  # Poprawiona giełda
            interval=INTERVAL
        )

    def fetch_data(self):
        try:
            analysis = self.handler.get_analysis()
            self.data = {
                'RSI': analysis.indicators['RSI'],
                'MACD': analysis.indicators['MACD.macd'],
                'Signal': analysis.indicators['MACD.signal'],
                'ATR': analysis.indicators.get('ATR', np.random.uniform(0.5, 2.0)),
                'Close': analysis.indicators['close'],
                'Volume': analysis.indicators.get('volume', np.random.uniform(50000, 100000))
            }
            logging.info(f"Pobrano dane z TradingView dla {self.symbol}")
            return True
        except Exception as e:
            logging.error(f"Błąd pobierania danych dla {self.symbol}: {str(e)}")
            return False

    def analyze_trend(self):
        try:
            current = self.data
            signals = []
            score = 0

            # RSI
            rsi = current['RSI']
            if rsi > 60:
                signals.append(f"RSI: Sprzed
