import yfinance as yf
import pandas as pd
import requests

# Konfiguracja Telegrama
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"  # Token bota
CHAT_ID = "-1002655090041"  # ID czatu

# Parametry analizy
symbols = {
    "US30 (Dow Jones)": "^DJI",
    "DAX (Germany 40)": "^GDAXI"
}
interval = "5m"  # Interwał 5 minut
lookback = "2d"   # Dane z ostatnich 2 dni

def calculate_rsi(data, window=14):
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_gain = up.rolling(window).mean()
    avg_loss = down.rolling(window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data):
    ema12 = data.ewm(span=12, adjust=False).mean()
    ema26 = data.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line

def analyze_trend(symbol, data):
    close = data["Close"]
    rsi = calculate_rsi(close)
    macd_line, signal_line = calculate_macd(close)

    rsi_current = float(rsi.iloc[-1])
    macd_current = float(macd_line.iloc[-1])
    signal_current = float(signal_line.iloc[-1])
    prev_macd = float(macd_line.iloc[-2])
    prev_signal = float(signal_line.iloc[-2])

    # Warunki zmiany trendu
    trend_signal = ""
    if rsi_current < 30 and macd_current > signal_current and prev_macd <= prev_signal:
        trend_signal = "Potencjalna zmiana trendu: sygnał kupna!"
    elif rsi_current > 70 and macd_current < signal_current and prev_macd >= prev_signal:
        trend_signal = "Potencjalna zmiana trendu: sygnał sprzedaży!"

    # Tworzenie tekstu analizy
    if trend_signal:
        analysis_text = (
            f"Zmiana trendu na {symbol} (5m interwał):\n"
            f"RSI (5m): {rsi_current:.2f}\n"
            f"MACD: {macd_current:.2f}, Sygnał: {signal_current:.2f}\n"
            f"{trend_signal}"
        )
        return analysis_text
    return None
# Sprawdzenie pobrania danych
print("Pobieram dane z Yahoo Finance...")

# Pobierz dane i przeprowadź analizę dla obu indeksów
analysis_messages = []
for name, ticker in symbols.items():
    print(f"Pobieram dane dla {name} ({ticker})...")
    data = yf.download(ticker, period=lookback, interval=interval)
    
    if data is None or data.empty:
        print(f"Brak danych dla {name}!")
        continue

    print(f"Dane dla {name} pobrane pomyślnie. Ostatnie wartości:")
    print(data.tail())  # Wyświetl ostatnie wiersze danych

    # Dodatkowa kontrola danych
    try:
        print(f"Ostatnia cena zamknięcia dla {name}: {data['Close'].iloc[-1]}")
    except Exception as e:
        print(f"Błąd odczytu ceny zamknięcia dla {name}: {e}")

    analysis = analyze_trend(name, data)
    if analysis:
        print(f"Wykryto zmianę trendu dla {name}!")
        analysis_messages.append(analysis)
    else:
        print(f"Brak zmiany trendu dla {name}.")
