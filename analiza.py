import os
import yfinance as yf
from telegram import Bot

def wyslij_analize():
    # Pobierz token i ID czatu z zmiennych środowiskowych
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    ID_CZATU = os.getenv("ID_CZATU")

    # Pobierz dane giełdowe z Yahoo Finance
    dane = yf.download("^DJI", period="1d")
    
    # Upewnij się, że dane są poprawne i nie są puste
    if not dane.empty:
        # Pobierz ostatnią cenę zamknięcia jako liczba float
        cena = float(dane['Close'].iloc[-1])

        # Przygotuj treść wiadomości
        tekst = f"Analiza US30 (Dow Jones):\nCena zamknięcia: {cena:.2f}"
        print(f"Wiadomość: {tekst}")

        # Utwórz bota i wyślij wiadomość
        try:
            bot = Bot(token=TOKEN_TELEGRAM)
            bot.send_message(chat_id=ID_CZATU, text=tekst)
            print("Wiadomość wysłana pomyślnie")
        except Exception as e:
            print(f"Błąd przy wysyłaniu: {e}")
    else:
        print("Błąd: Brak danych giełdowych.")

# Uruchom funkcję
wyslij_analize()
