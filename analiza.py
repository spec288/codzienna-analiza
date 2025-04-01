import numpy as np
import logging

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

        # RSI
        rsi = current.get('RSI', np.nan)
        if not np.isnan(rsi):
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
        macd = current.get('MACD', np.nan)
        signal = current.get('Signal', np.nan)
        if not np.isnan(macd) and not np.isnan(signal):
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

        # Trend - EMA50
        ema50 = current.get('EMA50', np.nan)
        if not np.isnan(ema50):
            if price > ema50:
                signals.append(f"Trend: Wzrostowy (Cena > EMA50)")
                score += 1
            else:
                signals.append(f"Trend: Spadkowy (Cena < EMA50)")
                score -= 1
        else:
            signals.append("EMA50: Brak danych")

        # Stochastic Oscillator
        stochastic = current.get('Stochastic', np.nan)
        if not np.isnan(stochastic):
            if stochastic > 80:
                signals.append(f"Stochastic: Sprzedaj ({stochastic:.2f}) - Przegrzany rynek")
                score -= 1
            elif stochastic < 20:
                signals.append(f"Stochastic: Kup ({stochastic:.2f}) - Wyprzedany rynek")
                score += 1
            else:
                signals.append(f"Stochastic: Neutralne ({stochastic:.2f})")
        else:
            signals.append("Stochastic: Brak danych")

        # ATR - Zmienność
        atr = current.get('ATR', np.nan)
        if not np.isnan(atr):
            signals.append(f"ATR (Zm) - Zmienność: {atr:.2f}")
        else:
            signals.append("ATR: Brak danych")

        # Wolumen
        volume = int(current.get('Volume', 0))
        signals.append(f"Wolumen: {volume}")

        # Ocena końcowa
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
        else:
            suggestion = "Neutralne"

        signals.append(f"Ocena końcowa: {suggestion} (Wynik: {score})")
        return suggestion, signals

    except Exception as e:
        logging.error(f"Błąd w analizie trendu: {str(e)}")
        return "Błąd analizy", ["Brak danych"]
