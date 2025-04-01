import pandas as pd
import numpy as np
import requests
import logging
from tradingview_ta import TA_Handler, Interval, Exchange
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
            exchange="OANDA",
            interval=INTERVAL
        )

    def fetch_data(self):
        try:
            analysis = self.handler.get_analysis()
            self.data = {
                'RSI': analysis.indicators['RSI'],
                'MACD': analysis.indicators['MACD.macd'],
                'Signal': analysis.indicators['MACD.signal'],
                'Volatility': analysis.indicators['Volatility'],
                'Close': analysis.indicators['close'],
                'Volume': analysis.indicators['volume']
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
                signals.append(f"RSI: Sprzedaj ({rsi:.2f})")
                score -= 2
            elif rsi < 40:
                signals.append(f"RSI: Kup ({rsi:.2f})")
                score += 2
            else:
                signals.append(f"RSI: Neutralne ({rsi:.2f})")

            # MACD
            macd = current['MACD']
            signal = current['Signal']
            if macd > signal:
                signals.append("MACD: Kup")
                score += 1.5
            else:
                signals.append("MACD: Sprzedaj")
                score -= 1.5

            # Volatility (sztuczne obliczenie)
            volatility = np.random.uniform(0.5, 1.5)  # Placeholder
            if volatility > 1:
                signals.append(f"Zmienność: Wysoka ({volatility:.2f}) (Kup)")
                score += 1
            else:
                signals.append(f"Zmienność: Niska ({volatility:.2f}) (Neutralne)")

            # Wolumen
            volume = current['Volume']
            if volume > 100000:
                signals.append("Wolumen: Wysoki (Kup)")
                score += 1
            elif volume < 10000:
                signals.append("Wolumen: Niski (Sprzedaj)")
                score -= 1
            else:
                signals.append("Wolumen: Średni (Neutralne)")

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
            logging.info(f"Wysłano wiadomość: {message}")
        except Exception as e:
            logging.error(f"Błąd wysyłania wiadomości: {str(e)}")

def main():
    notifier = TelegramNotifier(TOKEN, CHAT_ID)
    for symbol, ticker in SYMBOLS.items():
        analyzer = TradingViewAnalyzer(symbol, ticker)
        if analyzer.fetch_data():
            suggestion, signals, current = analyzer.analyze_trend()
            message = f"<b>{symbol} - {suggestion}</b>\n" + "\n".join(signals)
            notifier.send_message(message)

if __name__ == "__main__":
    main()
