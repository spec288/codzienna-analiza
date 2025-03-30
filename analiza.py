import yfinance as yf
import pandas as pd
import requests

# Konfiguracja Telegram
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"  # Token bota
CHAT_ID = "-1002655090041"  # ID czatu

# Pobierz dane z Yahoo Finance
symbols = {
    "US30 (Dow Jones)": "^DJI",
    "DAX": "^GDAXI"
}
period = "60d"
interval = "1d"

analyses = []
for name, symbol in symbols.items():
    data = yf.download(symbol, period=period, interval=interval, progress=False)
    if data is None or data.empty:
        analyses.append(f"{name} - Brak danych")
        continue

    close = data['Close']

    # Oblicz RSI (14)
    window = 14
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_gain = up.rolling(window).mean()
    avg_loss = down.rolling(window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_current = rsi.iloc[-1]  # Wyciągnięcie ostatniej wartości RSI jako liczby

    # Opis RSI
    if float(rsi_current) > 70:
        rsi_desc = "wykupiony"
    elif float(rsi_current) < 30:
        rsi_desc = "wyprzedany"
    else:
        rsi_desc = "neutralny"

    # Oblicz MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_current = macd_line.iloc[-1]
    signal_current = signal_line.iloc[-1]

    # Interpretacja MACD
    macd_desc = ""
    if len(macd_line) > 1:
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]
        if macd_current > signal_current and prev_macd <= prev_signal:
            macd_desc = "MACD przeciął sygnał w górę (sygnał kupna)"
        elif macd_current < signal_current and prev_macd >= prev_signal:
            macd_desc = "MACD przeciął sygnał w dół (sygnał sprzedaży)"
        else:
            if macd_current > signal_current:
                macd_desc = "MACD powyżej linii sygnału (sygnał wzrostowy)"
            else:
                macd_desc = "MACD poniżej linii sygnału (sygnał spadkowy)"
    else:
        if macd_current > signal_current:
            macd_desc = "MACD powyżej linii sygnału (sygnał wzrostowy)"
        else:
            macd_desc = "MACD poniżej linii sygnału (sygnał spadkowy)"

    # Sugestia
    bull_condition = (rsi_current < 30) or (macd_current > signal_current)
    bear_condition = (rsi_current > 70) or (macd_current < signal_current)
    if bull_condition and not bear_condition:
        suggestion = "zaraz kup"
    elif bear_condition and not bull_condition:
        suggestion = "zaraz sprzedaj"
    else:
        suggestion = "obserwuj"

    # Bieżąca cena zamknięcia
    last_price = close.iloc[-1]

    # Złóż analizę tekstową dla indeksu
    analysis_text = (
        f"{name}:\n"
        f"Cena zamknięcia: {last_price:.2f} pkt.\n"
        f"RSI (14): {rsi_current:.2f} ({rsi_desc})\n"
        f"MACD (12, 26, 9): {macd_current:.2f}, sygnał: {signal_current:.2f} ({macd_desc})\n"
        f"Sugestia: {suggestion}"
    )
    analyses.append(analysis_text)

# Połącz analizy dla wszystkich indeksów w jedną wiadomość
message = "\n\n".join(analyses)

# Wyślij wiadomość na Telegram
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": message}
try:
    response = requests.post(url, data=payload)
    response.raise_for_status()
    print("Wiadomość wysłana pomyślnie!")
except requests.exceptions.RequestException as e:
    print(f"Błąd przy wysyłaniu wiadomości Telegram: {e}")
