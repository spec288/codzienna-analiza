import yfinance as yf
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime

# Konfiguracja
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"
CHAT_ID = "-1002655090041"
SYMBOLS = {
    "US30 (Dow Jones)": "^DJI",
    "DAX (Germany 40)": "^GDAXI"
}
INTERVAL = '5m'
LOOKBACK = '1d'

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trend_analysis.log'),
        logging.StreamHandler()
    ]
)

class MarketAnalyzer:
    def __init__(self, symbol, ticker):
        self.symbol = symbol
        self.ticker = ticker
        self.data = None

    def fetch_data(self):
        try:
            self.data = yf.download(
                self.ticker,
                period=LOOKBACK,
                interval=INTERVAL
            )
            if self.data.empty:
                raise ValueError("Brak danych z Yahoo Finance")
            logging.info(f"Pobrano dane z Yahoo Finance dla {self.symbol}")
            return True
        except Exception as e:
            logging.error(f"Błąd pobierania danych dla {self.symbol}: {str(e)}")
            return False

    def analyze_trend(self):
        try:
            current = self.data.iloc[-1]
            signals = []
            score = 0

            # Cena aktualna
            price = current['Close']
            if isinstance(price, pd.Series):
                price = price.iloc[-1]
            signals.append(f"Cena: {float(price):.2f}")

            # Obliczanie RSI
            delta = self.data['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14, min_periods=1).mean()
            avg_loss = loss.rolling(window=14, min_periods=1).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            # Zabezpieczenie przed pustą wartością
            if pd.isna(current_rsi):
                current_rsi = 50

            # Sprawdzanie typu RSI
            if isinstance(current_rsi, pd.Series):
                current_rsi = current_rsi.iloc[-1]

            # Warunki RSI
            if current_rsi > 70:
                signals.append(f"RSI: Sprzedaj ({current_rsi:.2f})")
                score -= 2
            elif current_rsi < 30:
                signals.append(f"RSI: Kup ({current_rsi:.2f})")
                score += 2
            else:
                signals.append(f"RSI: Neutralne ({current_rsi:.2f})")

            # EMA 50
            ema50 = self.data['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            if isinstance(ema50, pd.Series):
                ema50 = ema50.iloc[-1]
            if price > ema50:
                signals.append(f"Trend: Wzrostowy (Cena > EMA50)")
                score += 1
            else:
                signals.append(f"Trend: Spadkowy (Cena < EMA50)")
                score -= 1

            # Wolumen
            volume = current['Volume']
            if isinstance(volume, pd.Series):
                volume = volume.iloc[-1]
            signals.append(f"Wolumen: {int(volume)}")

            # Ocena końcowa
            suggestion = "Neutralne"
            if score >= 3:
                suggestion = "Kupno"
            elif score <= -3:
                suggestion = "Sprzedaż"

            return suggestion, signals
        except Exception as e:
            logging.error(f"Błąd w analizie trendu: {str(e)}")
            return "Błąd analizy", ["Brak danych"]

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id

    def send_message(self, message):
        try:
            payload = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            logging.info(f"Wysłano wiadomość: {message}")
        except Exception as e:
            logging.error(f"Błąd wysyłania wiadomości: {str(e)}")

def main():
    notifier = TelegramNotifier(TOKEN, CHAT_ID)
    for symbol, ticker in SYMBOLS.items():
        analyzer = MarketAnalyzer(symbol, ticker)
        if analyzer.fetch_data():
            suggestion, signals = analyzer.analyze_trend()
            message = f"<b>{symbol} - {suggestion}</b>\n" + "\n".join(signals)
            notifier.send_message(message)

if __name__ == "__main__":
    main()
