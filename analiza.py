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
    "US30 (Dow Jones)": ("US30USD", "OANDA"),
    "DAX (Germany 40)": ("GER40", "MARKETSCOM")
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
    def __init__(self, symbol, ticker, exchange):
        self.symbol = symbol
        self.ticker = ticker
        self.exchange = exchange
        self.handler = TA_Handler(
            symbol=ticker,
            screener="cfd",
            exchange=exchange,
            interval=INTERVAL
        )

    def fetch_data(self):
        try:
            analysis = self.handler.get_analysis()
            self.data = {
                'RSI': analysis.indicators.get('RSI', np.nan),
                'MACD': analysis.indicators.get('MACD.macd', np.nan),
                'Signal': analysis.indicators.get('MACD.signal', np.nan),
                'ATR': analysis.indicators.get('ATR', np.nan),
                'Close': analysis.indicators.get('close', np.nan),
                'EMA50': analysis.indicators.get('EMA50', np.nan),
                'ADX': analysis.indicators.get('ADX', np.nan),
                'StochRSI': analysis.indicators.get('Stoch.RSI', np.nan),
                'SAR': analysis.indicators.get('SAR', np.nan),
                'Volume': analysis.indicators.get('volume', np.nan)
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

            # Cena aktualna
            price = current['Close']
            signals.append(f"Cena: {price:.2f}")

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
            macd = current['MACD']
            signal = current['Signal']
            if macd > signal:
                signals.append("MACD: Kup")
                score += 1.5
            else:
                signals.append("MACD: Sprzedaj")
                score -= 1.5

            # EMA 50 i przecięcie świec
            ema50 = current['EMA50']
            if price > ema50:
                signals.append(f"Trend: Wzrostowy (Cena > EMA50)")
                score += 1
            else:
                signals.append(f"Trend: Spadkowy (Cena < EMA50)")
                score -= 1

            # ADX - siła trendu
            adx = current['ADX']
            if adx > 25:
                signals.append(f"ADX: Silny trend ({adx:.2f})")
                score += 1
            else:
                signals.append(f"ADX: Słaby trend ({adx:.2f})")

            # Stochastic RSI
            stoch_rsi = current['StochRSI']
            if stoch_rsi > 80:
                signals.append(f"Stoch RSI: Wykupienie ({stoch_rsi:.2f})")
                score -= 1
            elif stoch_rsi < 20:
                signals.append(f"Stoch RSI: Wyprzedanie ({stoch_rsi:.2f})")
                score += 1
            else:
                signals.append(f"Stoch RSI: Neutralne ({stoch_rsi:.2f})")

            # Parabolic SAR
            sar = current['SAR']
            if price > sar:
                signals.append(f"SAR: Wsparcie (Kup)")
                score += 1
            else:
                signals.append(f"SAR: Opor (Sprzedaj)")
                score -= 1

            # Wolumen
            volume = current['Volume']
            if volume > 100000:
                signals.append("Wolumen: Wysoki (Potwierdzenie)")
                score += 1
            elif volume < 50000:
                signals.append("Wolumen: Niski (Ostrzeżenie)")
                score -= 1
            else:
                signals.append("Wolumen: Średni (Neutralne)")

            # Ocena końcowa
            suggestion = "Neutralne"
            if score >= 5:
                suggestion = "Silny sygnał kupna"
            elif score >= 2:
                suggestion = "Kupno"
            elif score <= -2:
                suggestion = "Sprzedaż"
            elif score <= -5:
                suggestion = "Silny sygnał sprzedaży"

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
    for symbol, (ticker, exchange) in SYMBOLS.items():
        analyzer = TradingViewAnalyzer(symbol, ticker, exchange)
        if analyzer.fetch_data():
            suggestion, signals, current = analyzer.analyze_trend()
            message = f"<b>{symbol} - {suggestion}</b>\n" + "\n".join(signals)
            notifier.send_message(message)

if __name__ == "__main__":
    main()
