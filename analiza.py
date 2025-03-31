import requests
import os
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Pobierz parametry z zmiennych środowiskowych lub użyj domyślnych
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "-1002655090041")

def send_telegram_message(message):
    """Prosta funkcja do wysyłania wiadomości bez złożonej klasy"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logging.info(f"Wiadomość wysłana! Status: {response.status_code}")
        return True
    except Exception as e:
        logging.error(f"Błąd wysyłania: {e}")
        return False

# Przykładowa wiadomość z analizy
message = """
<b>US30 (Dow Jones) - Sygnał kupna</b>
Cena: 42350.75
Wykryte sygnały:
• MACD dodatni
• Wyższy szczyt
• Prognoza wzrostowa
Wolumen: 5,432,100
Zmienność: 1.25%
"""

# Wyślij wiadomość
if send_telegram_message(message):
    print("Wiadomość z analizą wysłana pomyślnie!")
else:
    print("Nie udało się wysłać wiadomości z analizą.")
