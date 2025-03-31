import yfinance as yf import pandas as pd import requests

Konfiguracja Telegrama

TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU" CHAT_ID = "-1002655090041"

Parametry analizy

symbols = { "US30 (Dow Jones)": "^DJI", "DAX (Germany 40)": "^GDAXI" } interval = "5m" lookback = "2d"

Obliczanie wskaźników

def calculate_rsi(data, window=9): delta = data.diff() up = delta.clip(lower=0) down = -delta.clip(upper=0) avg_gain = up.rolling(window).mean() avg_loss = down.rolling(window).mean() rs = avg_gain / avg_loss rsi = 100 - (100 / (1 + rs)) return rsi

def calculate_macd(data): ema5 = data.ewm(span=5, adjust=False).mean() ema13 = data.ewm(span=13, adjust=False).mean() macd_line = ema5 - ema13 signal_line = macd_line.ewm(span=4, adjust=False).mean() return macd_line, signal_line

def calculate_ema(data, period): return data.ewm(span=period, adjust=False).mean()

def calculate_stochastic_rsi(data, window=9): min_val = data.rolling(window).min() max_val = data.rolling(window).max() stochastic_rsi = 100 * (data - min_val) / (max_val - min_val) return stochastic_rsi

def analyze_trend(symbol, data): close = data["Close"] rsi = calculate_rsi(close) macd_line, signal_line = calculate_macd(close) ema20 = calculate_ema(close, 20) ema50 = calculate_ema(close, 50) stochastic_rsi = calculate_stochastic_rsi(rsi)

try:
    rsi_current = rsi.iloc[-1]
    macd_current = macd_line.iloc[-1]
    signal_current = signal_line.iloc[-1]
    ema20_current = ema20.iloc[-1]
    ema50_current = ema50.iloc[-1]
    stoch_rsi_current = stochastic_rsi.iloc[-1]

    trend_signal = ""
    if (rsi_current < 30 or stoch_rsi_current < 20 or (macd_current > signal_current)) and ema20_current > ema50_current:
        trend_signal = "Potencjalny sygnał kupna!"
    elif (rsi_current > 70 or stoch_rsi_current > 80 or (macd_current < signal_current)) and ema20_current < ema50_current:
        trend_signal = "Potencjalny sygnał sprzedaży!"

    if trend_signal:
        analysis_text = (
            f"Zmiana trendu na {symbol} (5m interwał):\n"
            f"Cena: {close.iloc[-1]:.2f}\n"
            f"RSI: {rsi_current:.2f}\n"
            f"Stochastic RSI: {stoch_rsi_current:.2f}\n"
            f"MACD: {macd_current:.2f}, Sygnał: {signal_current:.2f}\n"
            f"EMA20: {ema20_current:.2f}, EMA50: {ema50_current:.2f}\n"
            f"{trend_signal}"
        )
        return analysis_text
except Exception as e:
    print(f"Błąd podczas analizy trendu dla {symbol}: {e}")

return None

analysis_messages = [] for name, ticker in symbols.items(): try: data = yf.download(ticker, period=lookback, interval=interval) if data.empty: message = f"Błąd: brak danych dla {name}." requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": message}) continue analysis = analyze_trend(name, data) if analysis: analysis_messages.append(analysis) except Exception as e: print(f"Błąd podczas pobierania danych dla {name}: {e}")

if analysis_messages: message = "\n\n".join(analysis_messages) else: message = "Brak sygnałów zmiany trendu - monitoring ciągły."

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage" payload = {"chat_id": CHAT_ID, "text": message}

try: response = requests.post(url, data=payload) response.raise_for_status() print("Wiadomość wysłana pomyślnie!") except requests.RequestException as e: print(f"Błąd wysyłania wiadomości: {e}")

