import os
import yfinance as yf
import requests

def wyslij_analize():
    # Pobierz token i ID czatu z zmiennych środowiskowych
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    ID_CZATU = os.getenv("ID_CZATU")

    # Pobierz dane giełdowe z Yahoo Finance
    dane = yf.download("^DJI", period="1d")
    if not dane.empty:
        # Pobierz ostatnią cenę zamknięcia jako liczba float
        cena = float(dane['Close'].iloc[-1])

        # Przygotuj treść wiadomości
        tekst = f"Analiza US30 (Dow Jones):\nCena zamknięcia: {cena:.2f}"

        # Wykonaj bezpośrednie żądanie HTTP do API Telegrama
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        params = {
            "chat_id": ID_CZATU,
            "text": tekst
        }

        try:
            response = requests.post(url, data=params)
            if response.status_code == 200:
                print("Wiadomość wysłana pomyślnie!")
            else:
                print(f"Błąd przy wysyłaniu: {response.json()}")
        except Exception as e:
            print(f"Błąd połączenia: {e}")
    else:
        print("Błąd: Brak danych giełdowych.")

# Uruchom funkcję
wyslij_analize()
