import yfinance as yf
import pandas as pd
import numpy as np
import requests

# Telegram Bot credentials (wprowadź właściwy token i chat_id)
BOT_TOKEN = "TWOJ_TOKEN_BOTA"
CHAT_ID = "TWOJE_CHAT_ID"

# Yahoo Finance ticker symbols for US30 (Dow Jones) and DAX
ticker_US30 = "^DJI"    # Dow Jones Industrial Average
ticker_DAX = "^GDAXI"   # German DAX Index

# Download recent data (ostatnie 60 dni dziennych notowań)
data_us30 = yf.download(ticker_US30, period="60d")
data_dax = yf.download(ticker_DAX, period="60d")

# Calculate RSI and MACD for US30 (Dow Jones)
close_us30 = data_us30["Close"]
# RSI 14-dniowy
delta_us30 = close_us30.diff()
up_us30 = delta_us30.clip(lower=0)
down_us30 = -delta_us30.clip(upper=0)
avg_gain_us30 = up_us30.rolling(window=14).mean()
avg_loss_us30 = down_us30.rolling(window=14).mean()
rs_us30 = avg_gain_us30 / avg_loss_us30
rsi_us30 = 100 - (100 / (1 + rs_us30))
# MACD (12, 26, 9)
ema12_us30 = close_us30.ewm(span=12, adjust=False).mean()
ema26_us30 = close_us30.ewm(span=26, adjust=False).mean()
macd_line_us30 = ema12_us30 - ema26_us30
signal_line_us30 = macd_line_us30.ewm(span=9, adjust=False).mean()
hist_us30 = macd_line_us30 - signal_line_us30

# Extract current indicator values (as floats)
rsi_current_us30 = float(rsi_us30.iloc[-1])
macd_current_us30 = float(macd_line_us30.iloc[-1])
signal_current_us30 = float(signal_line_us30.iloc[-1])
prev_macd_us30 = float(macd_line_us30.iloc[-2])
prev_signal_us30 = float(signal_line_us30.iloc[-2])

# Analyze US30 indicators
analysis_us30 = "US30 (Dow Jones): "
if rsi_current_us30 > 70:
    analysis_us30 += f"RSI={rsi_current_us30:.2f} (overbought). "
elif rsi_current_us30 < 30:
    analysis_us30 += f"RSI={rsi_current_us30:.2f} (oversold). "
else:
    analysis_us30 += f"RSI={rsi_current_us30:.2f}. "
if macd_current_us30 > signal_current_us30 and prev_macd_us30 < prev_signal_us30:
    analysis_us30 += f"MACD bullish crossover (MACD={macd_current_us30:.2f}, Signal={signal_current_us30:.2f})."
elif macd_current_us30 < signal_current_us30 and prev_macd_us30 > prev_signal_us30:
    analysis_us30 += f"MACD bearish crossover (MACD={macd_current_us30:.2f}, Signal={signal_current_us30:.2f})."
else:
    if macd_current_us30 > signal_current_us30:
        analysis_us30 += f"MACD above Signal (MACD={macd_current_us30:.2f}, Signal={signal_current_us30:.2f})."
    else:
        analysis_us30 += f"MACD below Signal (MACD={macd_current_us30:.2f}, Signal={signal_current_us30:.2f})."

# Calculate RSI and MACD for DAX
close_dax = data_dax["Close"]
# RSI 14-dniowy
delta_dax = close_dax.diff()
up_dax = delta_dax.clip(lower=0)
down_dax = -delta_dax.clip(upper=0)
avg_gain_dax = up_dax.rolling(window=14).mean()
avg_loss_dax = down_dax.rolling(window=14).mean()
rs_dax = avg_gain_dax / avg_loss_dax
rsi_dax = 100 - (100 / (1 + rs_dax))
# MACD (12, 26, 9)
ema12_dax = close_dax.ewm(span=12, adjust=False).mean()
ema26_dax = close_dax.ewm(span=26, adjust=False).mean()
macd_line_dax = ema12_dax - ema26_dax
signal_line_dax = macd_line_dax.ewm(span=9, adjust=False).mean()
hist_dax = macd_line_dax - signal_line_dax

# Extract current indicator values (as floats)
rsi_current_dax = float(rsi_dax.iloc[-1])
macd_current_dax = float(macd_line_dax.iloc[-1])
signal_current_dax = float(signal_line_dax.iloc[-1])
prev_macd_dax = float(macd_line_dax.iloc[-2])
prev_signal_dax = float(signal_line_dax.iloc[-2])

# Analyze DAX indicators
analysis_dax = "DAX (Germany 40): "
if rsi_current_dax > 70:
    analysis_dax += f"RSI={rsi_current_dax:.2f} (overbought). "
elif rsi_current_dax < 30:
    analysis_dax += f"RSI={rsi_current_dax:.2f} (oversold). "
else:
    analysis_dax += f"RSI={rsi_current_dax:.2f}. "
if macd_current_dax > signal_current_dax and prev_macd_dax < prev_signal_dax:
    analysis_dax += f"MACD bullish crossover (MACD={macd_current_dax:.2f}, Signal={signal_current_dax:.2f})."
elif macd_current_dax < signal_current_dax and prev_macd_dax > prev_signal_dax:
    analysis_dax += f"MACD bearish crossover (MACD={macd_current_dax:.2f}, Signal={signal_current_dax:.2f})."
else:
    if macd_current_dax > signal_current_dax:
        analysis_dax += f"MACD above Signal (MACD={macd_current_dax:.2f}, Signal={signal_current_dax:.2f})."
    else:
        analysis_dax += f"MACD below Signal (MACD={macd_current_dax:.2f}, Signal={signal_current_dax:.2f})."

# Combine analyses and send via Telegram
analysis_message = analysis_us30 + "\n" + analysis_dax
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": analysis_message}
requests.post(url, data=payload)
