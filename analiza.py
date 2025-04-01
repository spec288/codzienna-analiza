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
INTERVAL = '1m'  # Interwał 1 minuta
LOOKBACK_DAYS = 1  # Jeden dzień na potrzeby testu

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
            logging.info(f"Pobrano {len(self.data)} punktów danych dla {self.symbol}")
            logging.info(f"Przykładowe dane: \n{self.data.tail(5)}")
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

        try:
            if window_length >= min_window:
                self.data['Smooth_Close'] = savgol_filter(
                    self.data['Close'], 
                    window_length, 
                    3, 
                    mode='nearest'
                )
                logging.info(f"Zastosowano savgol_filter z oknem: {window_length}")
            else:
                self.data['Smooth_Close'] = self.data['Close']
                logging.warning(f"Za mało danych do filtra S-G ({available_points} punktów).")
        except Exception as e:
            logging.warning(f"Błąd filtru Savitzky-Golay: {str(e)}")
            self.data['Smooth_Close'] = self.data['Close']

        self.data['Volatility'] = self.data['Close'].pct_change().rolling(14).std().fillna(0)
        self.data['Volume'] = self.data['Volume'].fillna(0)
        volume_scaler = MinMaxScaler(feature_range=(0, 1))
        self.data['Norm_Volume'] = volume_scaler.fit_transform(self.data[['Volume']])

    def _calculate_rsi(self, series, period):
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
        avg_loss = avg_loss.replace(0, 1e-10)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    def calculate_adaptive_indicators(self):
        try:
            self.data['RSI'] = self._calculate_rsi(self.data['Close'], 14)
            logging.info(f"Obliczono RSI dla {self.symbol}, ostatnia wartość: {self.data['RSI'].iloc[-1]}")
        except Exception as e:
            logging.error(f"Błąd obliczania RSI: {str(e)}")

    def analyze_trend(self):
        current = self.data.iloc[-1]
        signals = []
        score = 0

        # Sprawdzenie wartości RSI i logowanie
        if 'RSI' in current:
            try:
                rsi_value = float(current['RSI'])  # Rzutowanie na float
                logging.info(f"RSI dla {self.symbol}: {rsi_value}")
                if rsi_value > 70:
                    score -= 2
                    signals.append(f"RSI wyprzedanie (sprzedaż) - wartość: {rsi_value:.2f}")
                elif rsi_value < 30:
                    score += 2
                    signals.append(f"RSI wykupienie (kupno) - wartość: {rsi_value:.2f}")
                else:
                    signals.append(f"RSI neutralne - wartość: {rsi_value:.2f}")
            except Exception as e:
                logging.warning(f"Błąd podczas analizy RSI dla {self.symbol}: {e}")
        else:
            logging.warning(f"Brak danych RSI dla {self.symbol}")

        # Generowanie sygnału
        logging.info(f"Suma punktów dla {self.symbol}: {score}")
        if score >= 2:
            return "Sygnał kupna", signals
        elif score <= -2:
            return "Sygnał sprzedaży", signals
        else:
            return "Brak wyraźnego sygnału", signals

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_message(self, message):
        try:
            payload = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            logging.info(f"Przygotowano wiadomość do wysłania: {message}")
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            logging.info(f"Wysłano wiadomość: {message}")
            return True
        except Exception as e:
            logging.error(f"Błąd wysyłania wiadomości: {str(e)}")
            return False

def main():
    notifier = TelegramNotifier(TOKEN, CHAT_ID)
    for symbol, ticker in SYMBOLS.items():
        analyzer = AdvancedMarketAnalyzer(symbol, ticker)
        if analyzer.fetch_data():
            analyzer.calculate_adaptive_indicators()
            signal, details = analyzer.analyze_trend()
            message = f"{symbol} - {signal}\n" + "\n".join(details)
            notifier.send_message(message)

if __name__ == "__main__":
    main()
