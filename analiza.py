import yfinance as yf
import requests

# Twoje dane z Telegrama
TOKEN_TELEGRAM = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"
ID_CZATU = "-1002655090041"

def wyslij_analize():
    try:
        # Pobierz dane giełdowe z Yahoo Finance
        dane = yf.download("^DJI", period="1d")
        
        # Sprawdź, czy dane są prawidłowe
        if not dane.empty:
            # Pobierz ostatnią cenę zamknięcia jako liczba float
            cena = float(dane['Close'].iloc[-1])

            # Przygotuj treść wiadomości
            tekst = f"Analiza US30 (Dow Jones):\nCena zamknięcia: {cena:.2f}"
            print(f"Wiadomość: {tekst}")

            # Wykonaj bezpośrednie żądanie HTTP do API Telegrama
            url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
            params = {
                "chat_id": ID_CZATU,
                "text": tekst
            }

            response = requests.post(url, data=params)

            # Sprawdź odpowiedź
            if response.status_code == 200:
                print("Wiadomość wysłana pomyślnie!")
            else:
                print(f"Błąd przy wysyłaniu: {response.json()}")
        else:
            print("Błąd: Brak danych giełdowych.")
    except Exception as e:
        print(f"Błąd połączenia: {e}")

# Uruchom funkcję
wyslij_analize()
