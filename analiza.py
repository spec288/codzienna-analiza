# Sprawdzenie pobrania danych
print("Pobieram dane z Yahoo Finance...")

# Pobierz dane i przeprowadź analizę dla obu indeksów
analysis_messages = []
for name, ticker in symbols.items():
    print(f"Pobieram dane dla {name} ({ticker})...")
    data = yf.download(ticker, period=lookback, interval=interval)
    
    if data is None or data.empty:
        print(f"Brak danych dla {name}!")
        continue

    print(f"Dane dla {name} pobrane pomyślnie. Ostatnie wartości:")
    print(data.tail())

    analysis = analyze_trend(name, data)
    if analysis:
        print(f"Wykryto zmianę trendu dla {name}!")
        analysis_messages.append(analysis)
    else:
        print(f"Brak zmiany trendu dla {name}.")
