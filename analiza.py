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

    try:
        rsi_current = float(rsi.iloc[-1].item())
        macd_current = float(macd_line.iloc[-1].item())
        signal_current = float(signal_line.iloc[-1].item())
        prev_macd = float(macd_line.iloc[-2].item())
        prev_signal = float(signal_line.iloc[-2].item())

        print(f"{symbol} - Ostatnia cena zamknięcia: {close.iloc[-1]}")
        print(f"RSI: {rsi_current}, MACD: {macd_current}, Signal: {signal_current}")
        print(f"Poprzedni MACD: {prev_macd}, Poprzedni sygnał: {prev_signal}")

        # Warunki zmiany trendu
        trend_signal = ""

        # Sygnał kupna: RSI < 30 lub MACD przecina sygnał od dołu
        if rsi_current < 30:
            trend_signal = "Potencjalny sygnał kupna: RSI wyprzedany!"
        elif macd_current > signal_current and prev_macd <= prev_signal:
            trend_signal = "Potencjalny sygnał kupna: MACD przecięło sygnał w górę!"

        # Sygnał sprzedaży: RSI > 70 lub MACD przecina sygnał od góry
        elif rsi_current > 70:
            trend_signal = "Potencjalny sygnał sprzedaży: RSI wykupiony!"
        elif macd_current < signal_current and prev_macd >= prev_signal:
            trend_signal = "Potencjalny sygnał sprzedaży: MACD przecięło sygnał w dół!"

        # Tworzenie tekstu analizy
        if trend_signal:
            analysis_text = (
                f"Zmiana trendu na {symbol} (5m interwał):\n"
                f"RSI (5m): {rsi_current:.2f}\n"
                f"MACD: {macd_current:.2f}, Sygnał: {signal_current:.2f}\n"
                f"{trend_signal}"
            )
            return analysis_text
        else:
            print(f"Brak wyraźnego sygnału zmiany trendu dla {symbol}.")
    except Exception as e:
        print(f"Błąd podczas analizy trendu dla {symbol}: {e}")

    return None


# Sprawdzenie pobrania danych
print("Pobieram dane z Yahoo Finance...")

# Pobierz dane i przeprowadź analizę dla obu indeksów
analysis_messages = []
for name, ticker in symbols.items():
    try:
        print(f"Pobieram dane dla {name} ({ticker}) z Yahoo Finance...")
        data = yf.download(ticker, period=lookback, interval=interval)
        
        if data is None or data.empty:
            print(f"Brak danych dla {name}!")
            continue

        print(f"Dane pobrane dla {name}:")
        print(data.tail())  # Wyświetl ostatnie wiersze danych

        # Ostatnia cena zamknięcia
        last_price = data['Close'].iloc[-1]
        print(f"Ostatnia cena zamknięcia dla {name}: {last_price}")

        analysis = analyze_trend(name, data)
        if analysis:
            print(f"Wykryto zmianę trendu dla {name}!")
            analysis_messages.append(analysis)
        else:
            print(f"Brak zmiany trendu dla {name}.")
    except Exception as e:
        print(f"Błąd podczas pobierania danych dla {name}: {e}")

# Test ręcznej wysyłki wiadomości bez względu na analizę
print("Przygotowuję wiadomość do wysłania (nawet jeśli brak analizy)...")
test_message = "Test wysyłki wiadomości bez względu na analizę."
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": test_message}

try:
    response = requests.post(url, data=payload)
    response.raise_for_status()
    print("Wiadomość testowa wysłana przed analizą!")
except requests.RequestException as e:
    print(f"Błąd wysyłania wiadomości testowej: {e}")

# Wysyłanie analizy (nawet jeśli brak zmiany trendu)
if analysis_messages:
    print("Przygotowuję wiadomość z analizą...")
    message = "\n\n".join(analysis_messages)
else:
    print("Brak zmiany trendu - wysyłka testowa")
    message = "Testowa wiadomość: brak zmiany trendu, ale wysyłam, by sprawdzić logikę."

print(f"Treść wiadomości:\n{message}")

try:
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    response.raise_for_status()
    print("Wiadomość wysłana pomyślnie!")
except requests.RequestException as e:
    print(f"Błąd wysyłania wiadomości: {e}")
