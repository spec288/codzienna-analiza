import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler

# Token bot Telegram
TOKEN = '8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU'

# ID czatu Telegram
CHAT_ID = '-1002655090041'

def analyze_us30():
    """Analiza indeksu US30."""
    ticker = yf.Ticker("YM=F")
    data = ticker.history(period="1d")
    
    rsi = RSIIndicator(data['Close'])
    macd = MACD(data['Close'])
    
    if rsi.rsi().iloc[-1] > 70:
        return "US30: Overbought"
    elif rsi.rsi().iloc[-1] < 30:
        return "US30: Oversold"
    else:
        return "US30: Neutral"

def analyze_dax():
    """Analiza indeksu DAX."""
    ticker = yf.Ticker("^GDAXI")
    data = ticker.history(period="1d")
    
    rsi = RSIIndicator(data['Close'])
    macd = MACD(data['Close'])
    
    if rsi.rsi().iloc[-1] > 70:
        return "DAX: Overbought"
    elif rsi.rsi().iloc[-1] < 30:
        return "DAX: Oversold"
    else:
        return "DAX: Neutral"

def send_telegram_message(message):
    """Wysyła wiadomość na Telegram."""
    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

def main():
    us30_status = analyze_us30()
    dax_status = analyze_dax()
    
    send_telegram_message(us30_status)
    send_telegram_message(dax_status)

if __name__ == "__main__":
    main()
