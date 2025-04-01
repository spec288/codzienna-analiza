def analyze_trend(self):
    try:
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
                signals.append(f"RSI: Sprzedaj ({rsi:.2f})")
                score -= 2
            elif rsi < 30:
                signals.append(f"RSI: Kup ({rsi:.2f})")
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
                signals.append("MACD: Kup")
                score += 1
            else:
                signals.append("MACD: Sprzedaj")
                score -= 1

        # Trend
        ema50 = current.get('EMA50', np.nan)
        if not np.isnan(ema50):
            if price > ema50:
                signals.append(f"Trend: Wzrostowy (Cena > EMA50)")
                score += 1
            else:
                signals.append(f"Trend: Spadkowy (Cena < EMA50)")
                score -= 1

        # Stochastic Oscillator
        stochastic = current.get('Stochastic', np.nan)
        if not np.isnan(stochastic):
            if stochastic > 80:
                signals.append(f"Stochastic: Sprzedaj ({stochastic:.2f})")
                score -= 1
            elif stochastic < 20:
                signals.append(f"Stochastic: Kup ({stochastic:.2f})")
                score += 1

        # ATR - Zmienność
        atr = current.get('ATR', np.nan)
        if not np.isnan(atr):
            signals.append(f"ATR: {atr:.2f}")

        # Wolumen
        volume = int(current.get('Volume', 0))
        signals.append(f"Wolumen: {volume}")

        # Ocena końcowa
        suggestion = "Neutralne"
        if score >= 4:
            suggestion = "Mocne Kupno"
        elif score == 3:
            suggestion = "Kupno"
        elif score <= -4:
            suggestion = "Mocna Sprzedaż"
        elif score == -3:
            suggestion = "Sprzedaż"

        return suggestion, signals
    except Exception as e:
        logging.error(f"Błąd w analizie trendu: {str(e)}")
        return "Błąd analizy", ["Brak danych"]
