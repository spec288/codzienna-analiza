import yfinance as yf
import pandas as pd
import numpy as np
import requests
from scipy.signal import savgol_filter
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
LOOKBACK_DAYS = 1

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

    def fetch_data(self):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=LOOKBACK_DAYS)
            self.data = yf.download(self.ticker, start=start_date, end=end_date, interval=INTERVAL, progress=False)
            if self.data.empty:
                raise ValueError("Brak danych z Yahoo Finance")
            logging.info(f"Pobrano {len(self.data)} punktów danych dla {self.symbol}")
            self._preprocess_data()
        except Exception as e:
            logging.error(f"Błąd pobierania danych dla {self.symbol}: {str(e)}")
            return False
        return True

    def _preprocess_data(self):
        self.data['Volatility'] = self.data['Close'].pct_change().rolling(14).std().fillna(0)
        self.data['Volume'] = self.data['Volume'].fillna(0)
        volume_scaler = MinMaxScaler(feature_range=(0, 1))
        self.data['Norm_Volume'] = volume_scaler.fit_transform(self.data[['Volume']])
        self.data['MACD'] = self.data['Close'].ewm(span=12).mean() - self.data['Close'].ewm(span=26).mean()
        self.data['Signal'] = self.data['MACD'].ewm(span=9).mean()

    def _calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    def calculate_indicators(self):
        self.data['RSI'] = self._calculate_rsi(self.data['Close'])

    def analyze_trend(self):
        try:
            current = self.data.iloc[-1]
            signals = []
            score = 0

            # RSI
            rsi = float(current['RSI'])
            if rsi > 60:
                signals.append(f"RSI: Sprzedaj ({rsi:.2f})")
                score -= 2
            elif rsi < 40:
                signals.append(f"RSI: Kup ({rsi:.2f})")
                score += 2
            else:
                signals.append(f"RSI: Neutralne ({rsi:.2f})")

            # MACD
            macd = float(current['MACD'])
            signal = float(current['Signal'])
            if macd > signal:
                signals.append("MACD: Kup")
                score += 1.5
            else:
                signals.append("MACD: Sprzedaj")
                score -= 1.5

            # Wolumen
            volume = float(current['Norm_Volume'])
            if volume > 0.8:
                signals.append("Wolumen: Wysoki (Kup)")
                score += 1
            elif volume < 0.2:
                signals.append("Wolumen: Niski (Sprzedaj)")
                score -= 1
            else:
                signals.append("Wolumen: Średni (Neutralne)")

            # Zmienność
            volatility = float(current['Volatility']) * 100
            if volatility > 1:
                signals.append(f"Zmienność: Wysoka ({volatility:.2f}%) (Kup)")
                score += 1
            else:
                signals.append(f"Zmienność: Niska ({volatility:.2f}%) (Neutralne)")

            suggestion = "Neutralne"
            if score > 5:
                suggestion = "Mocne Kupno"
            elif score > 2:
                suggestion = "Kupno"
            elif score < -2:
                suggestion = "Sprzedaż"
            elif score < -5:
                suggestion = "Mocna Sprzedaż"

            return suggestion, signals, current
        except Exception as e:
            logging.error(f"Błąd w analizie trendu: {str(e)}")
            return "Błąd analizy", ["Brak danych"], None

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_message(self, message):
        try:
            payload = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Błąd wysyłania wiadomości: {str(e)}")

def main():
    notifier = TelegramNotifier(TOKEN, CHAT_ID)
    for symbol, ticker in SYMBOLS.items():
        analyzer = AdvancedMarketAnalyzer(symbol, ticker)
        if analyzer.fetch_data():
            analyzer.calculate_indicators()
            suggestion, signals, current = analyzer.analyze_trend()
            message = f"<b>{symbol} - {suggestion}</b>\n" + "\n".join(signals)
            notifier.send_message(message)

if __name__ == "__main__":
    main()
