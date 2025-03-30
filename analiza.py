import os
import yfinance as yf
from telegram import Bot

def wyslij_analize():
    # Pobierz token i ID czatu z zmiennych środowiskowych
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    ID_CZATU = os.getenv("ID_CZATU")

    # Pobierz dane giełdowe z Yahoo Finance
    dane = yf.download("^DJI", period="1d")
    cena = dane['Close'].iloc[-1]  # Pobranie ostatniej wartości zamknięcia jako liczba

    # Przygotuj treść wiadomości
    tekst = f"Analiza US30 (Dow Jones):\nCena zamknięcia: {cena:.2f}"

    # Utwórz bota i wyślij wiadomość
    bot = Bot(token=TOKEN_TELEGRAM)
    bot.send_message(chat_id=ID_CZATU, text=tekst)

# Uruchom funkcję
wyslij_analize()
