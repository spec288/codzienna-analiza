import os
import yfinance as yf
from telegram import Bot

def wyslij_analize():
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    ID_CZATU = os.getenv("ID_CZATU")

    dane = yf.download("^DJI", period="1d")
    cena = dane['Close'].iloc[-1]

    tekst = f"Analiza US30 (Dow Jones):\nCena zamknięcia: {cena:.2f}"

    bot = Bot(token=TOKEN_TELEGRAM)
    bot.send_message(chat_id=ID_CZATU, text=tekst)

wyslij_analize()
