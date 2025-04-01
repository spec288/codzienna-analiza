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

    def calculate_indicators(self):
        # RSI
        delta = self.data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = self.data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = self.data['Close'].ewm(span=26, adjust=False).mean()
        self.data['MACD'] = ema12 - ema26
        self.data['Signal'] = self.data['MACD'].ewm(span=9, adjust=False).mean()

        # Zmienność
        self.data['Volatility'] = self.data['Close'].pct_change().rolling(14).std()

        # EMA 50
        self.data['EMA50'] = self.data['Close'].ewm(span=50, adjust=False).mean()

        # Stochastic Oscillator (poprawiony)
        low14 = self.data['Low'].rolling(window=14).min()
        high14 = self.data['High'].rolling(window=14).max()
        self.data['Stochastic'] = 100 * ((self.data['Close'] - low14) / (high14 - low14))

        # ATR
        self.data['ATR'] = self.data['High'].subtract(self.data['Low']).rolling(window=14).mean()

    def analyze_trend(self):
        try:
            self.calculate_indicators()
            current = self.data.iloc[-1]
            signals = []
            score = 0

            # Cena
            price = current['Close']
            signals.append(f"Cena: {float(price):.2f}")

            # RSI
            rsi = current['RSI']
            if rsi > 70:
                signals.append(f"RSI: Sprzedaj ({rsi:.2f})")
                score -= 2
            elif rsi < 30:
                signals.append(f"RSI: Kup ({rsi:.2f})")
                score += 2
            else:
                signals.append(f"RSI: Neutralne ({rsi:.2f})")

            # MACD
            if current['MACD'] > current['Signal']:
                signals.append("MACD: Kup")
                score += 1
            else:
                signals.append("MACD: Sprzedaj")
                score -= 1

            # Trend
            if price > current['EMA50']:
                signals.append(f"Trend: Wzrostowy (Cena > EMA50)")
                score += 1
            else:
                signals.append(f"Trend: Spadkowy (Cena < EMA50)")
                score -= 1

            # Stochastic Oscillator
            stochastic = current['Stochastic']
            if stochastic > 80:
                signals.append(f"Stochastic: Sprzedaj ({stochastic:.2f})")
                score -= 1
            elif stochastic < 20:
                signals.append(f"Stochastic: Kup ({stochastic:.2f})")
                score += 1

            # ATR - Zmienność
            atr = current['ATR']
            signals.append(f"ATR: {atr:.2f}")

            # Wolumen
            volume = current.get('Volume', 0)
            if volume == 0 or pd.isna(volume):
                signals.append("Wolumen: Brak danych")
            else:
                signals.append(f"Wolumen: {int(volume)}")

            # Ocena końcowa
            suggestion = "Neutralne"
            if score >= 4:
                suggestion = "Mocne Kupno"
            elif score == 3:
                suggestion = "Kupno"
            elif score <= -4:
                suggestion = "Mocna Sprzedaż"
            elif score == -3:
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
            requests.post(f"{self.base_url}/sendMessage", json=payload)
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
