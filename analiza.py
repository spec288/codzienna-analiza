import yfinance as yf
import pandas as pd
import numpy as np
import requests
from scipy.signal import savgol_filter, argrelextrema
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
import logging
from datetime import datetime, timedelta

# Konfiguracja
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"
CHAT_ID = "-1002655090041"
SYMBOLS = {
    "US30 (Dow Jones)": "^DJI",
    "DAX (Germany 40)": "^GDAXI"
}
INTERVAL = '5m'
LOOKBACK_DAYS = 3

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trend_analysis.log'),
        logging.StreamHandler()
    ]
)

class AdvancedMarketAnalyzer:
    def __init__(self, symbol, ticker):
        self.symbol = symbol
        self.ticker = ticker
        self.data = None
        self.indicators = {}
        
    def fetch_data(self):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=LOOKBACK_DAYS)
            self.data = yf.download(
                self.ticker,
                start=start_date,
                end=end_date,
                interval=INTERVAL,
                progress=False
            )
            if self.data.empty:
                raise ValueError("Brak danych z Yahoo Finance")
            self._preprocess_data()
        except Exception as e:
            logging.error(f"Błąd pobierania danych dla {self.symbol}: {str(e)}")
            return False
        return True

    def _preprocess_data(self):
        max_window = 21
        min_window = 5
        available_points = len(self.data)
        window_length = min(max_window, available_points)

        if window_length % 2 == 0:
            window_length -= 1

        if window_length >= min_window:
            try:
                self.data['Smooth_Close'] = savgol_filter(
                    self.data['Close'],
                    window_length,
                    3,
                    mode='nearest'
                )
            except Exception as e:
                logging.warning(f"Błąd filtru Savitzky-Golay: {str(e)}")
                self.data['Smooth_Close'] = self.data['Close']
        else:
            self.data['Smooth_Close'] = self.data['Close']
            logging.warning(f"Za mało danych ({available_points} punktów) do filtra S-G dla {self.symbol}.")

        self.data['Volatility'] = self.data['Close'].pct_change().rolling(14).std().fillna(0)
        self.data['Volume'] = self.data['Volume'].fillna(0)
        volume_scaler = MinMaxScaler(feature_range=(0, 1))
        self.data['Norm_Volume'] = volume_scaler.fit_transform(self.data[['Volume']])

    def _detect_price_patterns(self):
        if 'Smooth_Close' not in self.data.columns or len(self.data['Smooth_Close']) < 3:
            logging.warning(f"Za mało danych do wykrycia formacji cenowych dla {self.symbol}")
            return

        max_idx = argrelextrema(self.data['Smooth_Close'].values, np.greater)[0]
        min_idx = argrelextrema(self.data['Smooth_Close'].values, np.less)[0]

        self.data['Higher_High'] = False
        self.data['Lower_Low'] = False

        for idx in max_idx:
            try:
                current = float(self.data['Smooth_Close'].iloc[idx])
                prev = float(self.data['Smooth_Close'].iloc[idx - 1])
                if current > prev:
                    self.data.loc[self.data.index[idx], 'Higher_High'] = True
            except Exception as e:
                logging.warning(f"Błąd przy analizie Higher_High dla {self.symbol}: {e}")

        for idx in min_idx:
            try:
                current = float(self.data['Smooth_Close'].iloc[idx])
                prev = float(self.data['Smooth_Close'].iloc[idx - 1])
                if current < prev:
                    self.data.loc[self.data.index[idx], 'Lower_Low'] = True
            except Exception as e:
                logging.warning(f"Błąd przy analizie Lower_Low dla {self.symbol}: {e}")

    def analyze_trend(self):
        current = self.data.iloc[-1]
        signals = []
        score = 0

        if current['RSI'] < 30:
            score += 2
            signals.append("RSI wykupienie")
        elif current['RSI'] > 70:
            score -= 2
            signals.append("RSI wyprzedanie")

        if current['MACD'] > current['Signal']:
            score += 1
            signals.append("MACD dodatni")
        else:
            score -= 1
            signals.append("MACD ujemny")

        if current.get('Higher_High', False):
            score += 2
            signals.append("Wyższy szczyt")
        if current.get('Lower_Low', False):
            score -= 2
            signals.append("Niższy dołek")

        if score >= 4:
            return "Sygnał kupna", signals
        elif score <= -4:
            return "Sygnał sprzedaży", signals
        else:
            return "Brak wyraźnego sygnału", []

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_message(self, message):
        try:
            payload = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Błąd wysyłania wiadomości: {str(e)}")
            return False

def main():
    notifier = TelegramNotifier(TOKEN, CHAT_ID)
    for symbol, ticker in SYMBOLS.items():
        analyzer = AdvancedMarketAnalyzer(symbol, ticker)
        if analyzer.fetch_data():
            signal, details = analyzer.analyze_trend()
            message = f"{symbol} - {signal}\n" + "\n".join(details)
            notifier.send_message(message)

if __name__ == "__main__":
    main()
