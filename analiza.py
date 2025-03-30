import yfinance as yf
import pandas as pd
import numpy as np
import requests

# Konfiguracja Telegrama
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"  # Token bota
CHAT_ID = "-1002655090041"  # ID czatu

# Yahoo Finance ticker symbols for US30 (Dow Jones) and DAX
ticker_US30 = "^DJI"    # Dow Jones Industrial Average
ticker_DAX = "^GDAXI"   # German DAX Index

# Pobierz dane giełdowe (ostatnie 60 dni dziennych notowań)
data_us30 = yf.download(ticker_US30, period="60d")
data_dax = yf.download(ticker_DAX, period="60d")

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

def analyze(symbol, data):
    close = data["Close"]
    rsi = calculate_rsi(close)
    macd_line, signal_line = calculate_macd(close)

    rsi_current = float(rsi.iloc[-1])
    macd_current = float(macd_line.iloc[-1])
    signal_current = float(signal_line.iloc[-1])
    prev_macd = float(macd_line.iloc[-2])
    prev_signal = float(signal_line.iloc[-2])

    # RSI analiza
    if rsi_current > 70:
        rsi_desc = "wykupiony"
    elif rsi_current < 30:
        rsi_desc = "wyprzedany"
    else:
        rsi_desc = "neutralny"

    # MACD analiza
    if macd_current > signal_current and prev_macd <= prev_signal:
        macd_desc = "MACD przecięło sygnał w górę (sygnał kupna)"
    elif macd_current < signal_current and prev_macd >= prev_signal:
        macd_desc = "MACD przecięło sygnał w dół (sygnał sprzedaży)"
    elif macd_current > signal_current:
        macd_desc = "MACD powyżej linii sygnału (sygnał wzrostowy)"
    else:
        macd_desc = "MACD poniżej linii sygnału (sygnał spadkowy)"

    # Sugestia
    if rsi_current < 30 or (macd_current > signal_current and prev_macd <= prev_signal):
        suggestion = "zaraz kup"
    elif rsi_current > 70 or (macd_current < signal_current and prev_macd >= prev_signal):
        suggestion = "zaraz sprzedaj"
    else:
        suggestion = "obserwuj"

    # Bieżąca cena zamknięcia
    last_price = float(close.iloc[-1])

    analysis_text = (
        f"{symbol}:\n"
        f"Cena zamknięcia: {last_price:.2f} pkt\n"
        f"RSI (14): {rsi_current:.2f} ({rsi_desc})\n"
        f"MACD (12, 26, 9): {macd_current:.2f}, sygnał: {signal_current:.2f} ({macd_desc})\n"
        f"Sugestia: {suggestion}"
    )
    return analysis_text

# Analiza dla US30 i DAX
analysis_us30 = analyze("US30 (Dow Jones)", data_us30)
analysis_dax = analyze("DAX (Germany 40)", data_dax)

# Połącz analizy w jedną wiadomość
analysis_message = analysis_us30 + "\n\n" + analysis_dax

# Wyślij wiadomość na Telegram
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": analysis_message}

try:
    response = requests.post(url, data=payload)
    response.raise_for_status()
    print("Wiadomość wysłana pomyślnie!")
except requests.exceptions.RequestException as e:
    print(f"Błąd przy wysyłaniu wiadomości Telegram: {e}")
