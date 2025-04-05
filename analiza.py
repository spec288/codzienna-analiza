import requests
import logging
import os
from telegram import Bot

# Tokeny i klucze API - nie zaleca się trzymania ich w kodzie w dłuższej perspektywie czasowej
telegram_token = '7982983537:AAFwTZ81y0Jj33FKvODd-FpkJiVT57Mqk0g'
news_api_key = '904b75c6009240e3926ca2828abe7a5d'

# Klasa do analizy trendów
class TrendAnalyzer:
    def __init__(self, data):
        self.data = data  # DataFrame z danymi, np. cena, wolumen, wskaźniki

    def calculate_indicators(self):
        # Możesz dodać kod do obliczania wskaźników, jeśli chcesz
        pass

    def analyze_trend(self):
        try:
            # Oblicz wskaźniki
            self.calculate_indicators()

            current = self.data.iloc[-1]
            signals = []
            score = 0

            # Cena
            price = float(current['Close'])
            signals.append(f"Cena: {price:.2f}")

            # RSI (Relative Strength Index)
            rsi = current.get('RSI', None)
            if rsi is not None:
                if rsi > 70:
                    signals.append(f"RSI: Sprzedaj ({rsi:.2f}) - Przegrzany rynek")
                    score -= 2
                elif rsi < 30:
                    signals.append(f"RSI: Kup ({rsi:.2f}) - Wyprzedany rynek")
                    score += 2
                else:
                    signals.append(f"RSI: Neutralne ({rsi:.2f})")
            else:
                signals.append("RSI: Brak danych")

            # MACD
            macd = current.get('MACD', None)
            signal = current.get('Signal', None)
            if macd is not None and signal is not None:
                if macd > signal:
                    signals.append("MACD: Kup - Wzrost momentum")
                    score += 1
                elif macd < signal:
                    signals.append("MACD: Sprzedaj - Spadek momentum")
                    score -= 1
                else:
                    signals.append("MACD: Neutralne")
            else:
                signals.append("MACD: Brak danych")

            # EMA50
            ema50 = current.get('EMA50', None)
            if ema50 is not None:
                if price > ema50:
                    signals.append("EMA50: Wzrostowy trend")
                    score += 1
                else:
                    signals.append("EMA50: Spadkowy trend")
                    score -= 1
            else:
                signals.append("EMA50: Brak danych")

            # Wolumen
            volume = current.get('Volume', 0)
            signals.append(f"Wolumen: {volume}")

            # Ocena końcowa
            suggestion = "Neutralne"
            if score >= 4:
                suggestion = "Mocne Kupno"
            elif score == 3:
                suggestion = "Kupno"
            elif score == 2:
                suggestion = "Słabe Kupno"
            elif score == -2:
                suggestion = "Słaba Sprzedaż"
            elif score == -3:
                suggestion = "Sprzedaż"
            elif score <= -4:
                suggestion = "Mocna Sprzedaż"

            signals.append(f"Ocena końcowa: {suggestion} (Wynik: {score})")
            return suggestion, signals

        except Exception as e:
            logging.error(f"Błąd w analizie trendu: {str(e)}")
            return "Błąd analizy", ["Brak danych"]

# Funkcja do wysyłania danych na Telegram
def send_to_telegram(suggestion, signals, bot_token, chat_id):
    message = f"Analiza trendu:\n\n{suggestion}\n\n" + "\n".join(signals)
    bot = Bot(token=bot_token)
    bot.send_message(chat_id=chat_id, text=message)

# Funkcja do pobierania wiadomości z News API
def get_latest_news(api_key, query='financial'):
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        news = response.json()
        return news['articles']
    else:
        return []

# Funkcja główna
def main():
    # Zakładając, że masz DataFrame z danymi, np. `data`
    data = ...  # Załaduj dane (np. pandas DataFrame)
    analyzer = TrendAnalyzer(data)
    suggestion, signals = analyzer.analyze_trend()

    # Wyślij dane do Telegram
    chat_id = 'your_chat_id'  # Podaj swoje ID czatu
    send_to_telegram(suggestion, signals, telegram_token, chat_id)

    # Pobierz najnowsze wiadomości
    articles = get_latest_news(news_api_key)

    # Wyświetl tytuły wiadomości
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}\n")

# Uruchom główną funkcję
if __name__ == '__main__':
    main()
