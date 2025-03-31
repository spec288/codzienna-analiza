import yfinance as yf
import pandas as pd
import numpy as np
import requests
from scipy.signal import savgol_filter, argrelextrema
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
import logging
from datetime import datetime, timedelta

# Konfiguracja
TOKEN = "8170414773:AAGpuW4PUBJNcbkarA8x-P6D6I3_ke9XcOU"
CHAT_ID = "-1002655090041"
SYMBOLS = {
    "US30 (Dow Jones)": "^DJI",
    "DAX (Germany 40)": "^GDAXI"
}
INTERVAL = '5m'
LOOKBACK_DAYS = 3  # Możesz zmienić zakres pobieranych danych

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trend_analysis.log'),
        logging.StreamHandler()
    ]
)

class AdvancedMarketAnalyzer:
    def __init__(self, symbol, ticker):
        self.symbol = symbol
        self.ticker = ticker
        self.data = None
        self.indicators = {}
        
    def fetch_data(self):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=LOOKBACK_DAYS)
            self.data = yf.download(
                self.ticker,
                start=start_date,
                end=end_date,
                interval=INTERVAL,
                progress=False
            )
            if self.data.empty:
                raise ValueError("Brak danych z Yahoo Finance")
            self._preprocess_data()
        except Exception as e:
            logging.error(f"Błąd pobierania danych dla {self.symbol}: {str(e)}")
            return False
        return True

    def _preprocess_data(self):
        # Dynamiczne dostosowanie długości okna dla filtra Savitzky-Golay
        max_window = 21
        min_window = 5
        available_points = len(self.data)
        window_length = min(max_window, available_points)

        if window_length >= min_window:
            try:
                self.data['Smooth_Close'] = savgol_filter(
                    self.data['Close'], 
                    window_length, 
                    3, 
                    mode='nearest'
                )
                logging.info(f"Zastosowano savgol_filter z oknem: {window_length}")
            except Exception as e:
                logging.warning(f"Błąd filtru Savitzky-Golay dla {self.symbol}: {str(e)}")
                self.data['Smooth_Close'] = self.data['Close']
        else:
            self.data['Smooth_Close'] = self.data['Close']
            logging.warning(f"Za mało danych ({available_points} punktów) do filtra S-G dla {self.symbol}. Używamy wartości Close.")
        
        # Obliczanie zmienności – wypełniamy wartości NaN zerami
        self.data['Volatility'] = self.data['Close'].pct_change().rolling(14).std().fillna(0)
        
        # Normalizacja wolumenu – zabezpieczenie przed brakami danych
        self.data['Volume'] = self.data['Volume'].fillna(0)
        volume_scaler = MinMaxScaler(feature_range=(0, 1))
        self.data['Norm_Volume'] = volume_scaler.fit_transform(self.data[['Volume']])

    def calculate_adaptive_indicators(self):
        # Dynamiczne RSI – sprawdzamy, czy ostatnia zmienność jest sensowna
        last_volatility = self.data['Volatility'].iloc[-1]
        if pd.isna(last_volatility) or last_volatility <= 0:
            last_volatility = 0.1
            logging.warning(f"Brak lub zerowa zmienność dla {self.symbol}. Używam wartości domyślnej 0.1")
        rsi_period = max(9, int(14 * (1 - last_volatility)))
        self.data['RSI'] = self._calculate_rsi(self.data['Close'], rsi_period)
        
        # Adaptacyjne progi RSI
        self.data['RSI_Low'] = 35 - (self.data['Volatility'] * 100).clip(0, 15)
        self.data['RSI_High'] = 65 + (self.data['Volatility'] * 100).clip(0, 15)
        
        # MACD z dynamicznymi okresami
        fast = int(12 * (1 + last_volatility))
        slow = int(26 * (1 + last_volatility))
        self.data['MACD'] = self.data['Close'].ewm(span=fast).mean() - self.data['Close'].ewm(span=slow).mean()
        self.data['Signal'] = self.data['MACD'].ewm(span=9).mean()
        
        # Wykrywanie formacji cenowych
        self._detect_price_patterns()
        
        # Predykcja ARIMA
        self._calculate_arima_forecast()

    def _calculate_rsi(self, series, period):
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        # Wypełniamy wartości NaN neutralną wartością 50
        return rsi.fillna(50)

    def _detect_price_patterns(self):
        # Upewnij się, że mamy wystarczającą ilość danych
        if 'Smooth_Close' not in self.data.columns or len(self.data['Smooth_Close']) < 3:
            logging.warning(f"Za mało danych do wykrycia formacji cenowych dla {self.symbol}")
            self.data['Higher_High'] = False
            self.data['Lower_Low'] = False
            return
        
        max_idx = argrelextrema(self.data['Smooth_Close'].values, np.greater)[0]
        min_idx = argrelextrema(self.data['Smooth_Close'].values, np.less)[0]
        
        self.data['Higher_High'] = False
        self.data['Lower_Low'] = False
        
        for i in range(1, len(max_idx)):
            if self.data.iloc[max_idx[i]]['Smooth_Close'] > self.data.iloc[max_idx[i-1]]['Smooth_Close']:
                self.data.at[self.data.index[max_idx[i]], 'Higher_High'] = True
                
        for i in range(1, len(min_idx)):
            if self.data.iloc[min_idx[i]]['Smooth_Close'] < self.data.iloc[min_idx[i-1]]['Smooth_Close']:
                self.data.at[self.data.index[min_idx[i]], 'Lower_Low'] = True

    def _calculate_arima_forecast(self):
        try:
            # Sprawdzamy, czy mamy wystarczającą liczbę danych do modelu ARIMA
            if len(self.data['Close'].dropna()) < 30:
                raise ValueError("Za mało danych do modelu ARIMA")
            model = ARIMA(self.data['Close'].dropna(), order=(2, 1, 2))
            results = model.fit()
            forecast = results.get_forecast(steps=3)
            self.indicators['ARIMA_Forecast'] = forecast.predicted_mean.values
        except Exception as e:
            logging.warning(f"Błąd ARIMA dla {self.symbol}: {str(e)}")
            self.indicators['ARIMA_Forecast'] = None

    def analyze_trend(self):
        current = self.data.iloc[-1]
        signals = []
        score = 0
        
        # 1. Analiza RSI
        if current['RSI'] < current['RSI_Low']:
            score += 2
            signals.append('RSI wskazuje wykupienie')
        elif current['RSI'] > current['RSI_High']:
            score -= 2
            signals.append('RSI wskazuje wyprzedanie')
            
        # 2. MACD
        if current['MACD'] > current['Signal']:
            score += 1.5
            signals.append('MACD dodatni')
        else:
            score -= 1.5
            signals.append('MACD ujemny')
            
        # 3. Formacje cenowe
        if current.get('Higher_High', False):
            score += 2
            signals.append('Wyższy szczyt')
        if current.get('Lower_Low', False):
            score -= 2
            signals.append('Niższy dołek')
            
        # 4. Predykcja ARIMA
        if self.indicators.get('ARIMA_Forecast') is not None:
            if self.indicators['ARIMA_Forecast'].mean() > current['Close']:
                score += 1.5
                signals.append('Prognoza wzrostowa')
            else:
                score -= 1.5
                signals.append('Prognoza spadkowa')
                
        # 5. Analiza wolumenu
        if current['Norm_Volume'] > 0.8:
            score += 1.2
            signals.append('Wysoki wolumen')
        elif current['Norm_Volume'] < 0.2:
            score -= 1
            signals.append('Niski wolumen')
            
        # Generowanie sygnału na podstawie sumy punktów
        if score >= 6 and current['Norm_Volume'] > 0.7:
            return "SILNY SYGNAŁ KUPNA", signals
        elif score <= -6 and current['Norm_Volume'] > 0.7:
            return "SILNY SYGNAŁ SPRZEDAŻY", signals
        elif score >= 4:
            return "Sygnał kupna", signals
        elif score <= -4:
            return "Sygnał sprzedaży", signals
        else:
            return "Brak wyraźnego sygnału", []

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
        
    def send_message(self, message):
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"Błąd wysyłania wiadomości: {str(e)}")
            return False

def main():
    notifier = TelegramNotifier(TOKEN, CHAT_ID)
    
    for symbol, ticker in SYMBOLS.items():
        analyzer = AdvancedMarketAnalyzer(symbol, ticker)
        if not analyzer.fetch_data():
            continue
            
        analyzer.calculate_adaptive_indicators()
        signal, details = analyzer.analyze_trend()
        
        if "Brak" not in signal:
            current_price = analyzer.data['Close'].iloc[-1]
            message = "\n".join([
                f"<b>{symbol} - {signal}</b>",
                f"Cena: {current_price:.2f}",
                "Wykryte sygnały:",
                *details,
                f"Wolumen: {analyzer.data['Volume'].iloc[-1]:,.0f}",
                f"Zmienność: {analyzer.data['Volatility'].iloc[-1]*100:.2f}%"
            ])
            notifier.send_message(message)
        else:
            logging.info(f"{symbol}: Brak istotnych sygnałów")

if __name__ == "__main__":
    main()
