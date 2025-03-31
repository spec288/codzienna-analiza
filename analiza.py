import requests

# Token i chat ID
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"
CHAT_ID = "-1002655090041"

# Testowa wiadomość
message = "Test wiadomości - bezpośrednio ze skryptu"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": message}

try:
    response = requests.post(url, data=payload)
    response.raise_for_status()
    print("Wiadomość testowa wysłana!")
    print(f"Status: {response.status_code}, Odpowiedź: {response.json()}")
except requests.RequestException as e:
    print(f"Błąd wysyłania: {e}")
