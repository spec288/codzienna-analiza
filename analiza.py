import yfinance as yf
import pandas as pd
import numpy as np
import requests
from scipy.signal import savgol_filter, argrelextrema
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
import logging
import logging.handlers
import os
from datetime import datetime, timedelta

# Konfiguracja - odczyt z zmiennych środowiskowych
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Sprawdzenie zmiennych środowiskowych
if not TOKEN or not CHAT_ID:
    raise ValueError("Brak wymaganych zmiennych środowiskowych (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)")

SYMBOLS = {
    "US30 (Dow Jones)": "^DJI",
    "DAX (Germany 40)": "^GDAXI"
}
INTERVAL = '5m'
LOOKBACK_DAYS = 3

# Konfiguracja logowania
def setup_logging():
    logger = logging.getLogger('market_analyzer')
    logger.setLevel(logging.INFO)
    
    # Formatowanie logów
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler dla plików z rotacją
    file_handler = logging.handlers.RotatingFileHandler(
        'trend_analysis.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Handler dla konsoli
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

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
            return True
        except Exception as e:
            logger.error(f"Błąd pobierania danych dla {self.symbol}: {str(e)}")
            return False

    def _preprocess_data(self):
        try:
            # Dostosowanie długości okna dla filtra Savitzky-Golay
            max_window = 21
            min_window = 5
            available_points = len(self.data)
            window_length = min(max_window, available_points)
            
            # Upewnienie się, że długość okna jest nieparzysta
            if window_length % 2 == 0:
                window_length -= 1
                
            if window_length >= min_window:
                try:
                    self.data['Smooth_Close'] = savgol_filter(
                        self.data['Close'], 
                        window_length, 
                        3, 
                        mode='nearest'
                    )
                    logger.info(f"Zastosowano savgol_filter z oknem: {window_length}")
                except Exception as e:
                    logger.warning(f"Błąd filtru Savitzky-Golay dla {self.symbol}: {str(e)}")
                    self.data['Smooth_Close'] = self.data['Close']
            else:
                self.data['Smooth_Close'] = self.data['Close']
                logger.warning(f"Za mało danych ({available_points} punktów) do filtra S-G dla {self.symbol}")
            
            # Obliczanie zmienności – wypełniamy wartości NaN zerami
            self.data['Volatility'] = self.data['Close'].pct_change().rolling(14).std().fillna(0)
            
            # Normalizacja wolumenu
            self.data['Volume'] = self.data['Volume'].fillna(0)
            
            # Sprawdzenie czy wszystkie wartości wolumenu nie są zerami
            if self.data['Volume'].sum() > 0:
                volume_scaler = MinMaxScaler(feature_range=(0, 1))
                self.data['Norm_Volume'] = volume_scaler.fit_transform(self.data[['Volume']])
            else:
                logger.warning(f"Wszystkie wartości wolumenu są zerami dla {self.symbol}")
                self.data['Norm_Volume'] = 0
        except Exception as e:
            logger.error(f"Błąd przetwarzania danych dla {self.symbol}: {str(e)}")
            raise

    def calculate_adaptive_indicators(self):
        try:
            # Dynamiczne RSI
            last_volatility = self.data['Volatility'].iloc[-1]
            if pd.isna(last_volatility) or last_volatility <= 0:
                last_volatility = 0.1
                logger.warning(f"Brak lub zerowa zmienność dla {self.symbol}. Używam wartości 0.1")
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
            
            self._detect_price_patterns()
            self._calculate_arima_forecast()
        except Exception as e:
            logger.error(f"Błąd obliczania wskaźników dla {self.symbol}: {str(e)}")
            raise

    def _calculate_rsi(self, series, period):
        try:
            delta = series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
            avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
            
            # Zabezpieczenie przed dzieleniem przez zero
            avg_loss = avg_loss.replace(0, 1e-10)
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            # Wypełniamy wartości NaN neutralną wartością 50
            return rsi.fillna(50)
        except Exception as e:
            logger.error(f"Błąd obliczania RSI dla {self.symbol}: {str(e)}")
            # Zwracamy serię neutralnych wartości w przypadku błędu
            return pd.Series(50, index=series.index)

    def _detect_price_patterns(self):
        try:
            # Upewniamy się, że mamy wystarczającą ilość danych
            if 'Smooth_Close' not in self.data.columns or len(self.data['Smooth_Close']) < 3:
                logger.warning(f"Za mało danych do wykrycia formacji cenowych dla {self.symbol}")
                self.data['Higher_High'] = False
                self.data['Lower_Low'] = False
                return
            
            max_idx = argrelextrema(self.data['Smooth_Close'].values, np.greater)[0]
            min_idx = argrelextrema(self.data['Smooth_Close'].values, np.less)[0]
            
            self.data['Higher_High'] = False
            self.data['Lower_Low'] = False
            
            # Sprawdzamy kolejne maksima
            for i in range(1, len(max_idx)):
                try:
                    if max_idx[i] >= len(self.data.index):
                        continue
                    val_current = float(self.data['Smooth_Close'].iloc[max_idx[i]])
                    val_prev = float(self.data['Smooth_Close'].iloc[max_idx[i - 1]])
                    if val_current > val_prev:
                        # Używamy loc zamiast at
                        self.data.loc[self.data.index[max_idx[i]], 'Higher_High'] = True
                except Exception as e:
                    logger.warning(f"Błąd podczas analizy maksimów dla {self.symbol}: {e}")
                    continue
                    
            # Sprawdzamy kolejne minima
            for i in range(1, len(min_idx)):
                try:
                    if min_idx[i] >= len(self.data.index):
                        continue
                    val_current = float(self.data['Smooth_Close'].iloc[min_idx[i]])
                    val_prev = float(self.data['Smooth_Close'].iloc[min_idx[i - 1]])
                    if val_current < val_prev:
                        # Używamy loc zamiast at
                        self.data.loc[self.data.index[min_idx[i]], 'Lower_Low'] = True
                except Exception as e:
                    logger.warning(f"Błąd podczas analizy minimów dla {self.symbol}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Błąd wykrywania formacji cenowych dla {self.symbol}: {str(e)}")
            self.data['Higher_High'] = False
            self.data['Lower_Low'] = False

    def _calculate_arima_forecast(self):
        try:
            # Sprawdzamy, czy mamy wystarczającą liczbę danych do modelu ARIMA
            clean_data = self.data['Close'].dropna()
            if len(clean_data) < 30:
                logger.warning(f"Za mało danych do modelu ARIMA dla {self.symbol}: {len(clean_data)}")
                self.indicators['ARIMA_Forecast'] = None
                return
                
            model = ARIMA(clean_data, order=(2, 1, 2))
            results = model.fit()
            forecast = results.get_forecast(steps=3)
            self.indicators['ARIMA_Forecast'] = forecast.predicted_mean.values
            logger.info(f"Pomyślnie obliczono prognozę ARIMA dla {self.symbol}")
        except Exception as e:
            logger.warning(f"Błąd ARIMA dla {self.symbol}: {str(e)}")
            self.indicators['ARIMA_Forecast'] = None

    def analyze_trend(self):
        try:
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
                
            # 3. Formacje cenowe - bezpieczne sprawdzenie
            if 'Higher_High' in current and current['Higher_High']:
                score += 2
                signals.append('Wyższy szczyt')
            if 'Lower_Low' in current and current['Lower_Low']:
                score -= 2
                signals.append('Niższy dołek')
                
            # 4. Predykcja ARIMA
            if self.indicators.get('ARIMA_Forecast') is not None:
                forecast_mean = np.mean(self.indicators['ARIMA_Forecast'])
                if not np.isnan(forecast_mean) and forecast_mean > current['Close']:
                    score += 1.5
                    signals.append('Prognoza wzrostowa')
                elif not np.isnan(forecast_mean):
                    score -= 1.5
                    signals.append('Prognoza spadkowa')
                    
            # 5. Analiza wolumenu
            if current['Norm_Volume'] > 0.8:
                score += 1.2
                signals.append('Wysoki wolumen')
            elif current['Norm_Volume'] < 0.2:
                score -= 1
                signals.append('Niski wolumen')
                
            # Generowanie sygnału
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
        except Exception as e:
            logger.error(f"Błąd analizy trendu dla {self.symbol}: {str(e)}")
            return "Błąd analizy", []

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
        self.session = requests.Session()  # Używamy sesji dla wydajności
        
    def send_message(self, message):
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = self.session.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Błąd wysyłania wiadomości Telegram: {str(e)}")
            return False
            
    def __del__(self):
        # Zamykamy sesję przy niszczeniu obiektu
        self.session.close()

def main():
    try:
        logger.info("Rozpoczynam analizę rynkową")
        
        notifier = TelegramNotifier(TOKEN, CHAT_ID)
        
        for symbol, ticker in SYMBOLS.items():
            try:
                logger.info(f"Analizuję {symbol} ({ticker})")
                analyzer = AdvancedMarketAnalyzer(symbol, ticker)
                if not analyzer.fetch_data():
                    logger.warning(f"Pomijam analizę {symbol} - błąd pobierania danych")
                    continue
                    
                analyzer.calculate_adaptive_indicators()
                signal, details = analyzer.analyze_trend()
                
                if "Brak" not in signal and "Błąd" not in signal:
                    current_price = analyzer.data['Close'].iloc[-1]
                    message = "\n".join([
                        f"<b>{symbol} - {signal}</b>",
                        f"Cena: {current_price:.2f}",
                        "Wykryte sygnały:",
                        *details,
                        f"Wolumen: {analyzer.data['Volume'].iloc[-1]:,.0f}",
                        f"Zmienność: {analyzer.data['Volatility'].iloc[-1]*100:.2f}%"
                    ])
                    if notifier.send_message(message):
                        logger.info(f"Wysłano powiadomienie o sygnale {signal} dla {symbol}")
                    else:
                        logger.error(f"Nie udało się wysłać powiadomienia dla {symbol}")
                else:
                    logger.info(f"{symbol}: {signal}")
            except Exception as e:
                logger.error(f"Błąd podczas analizy {symbol}: {str(e)}")
                continue
        
        logger.info("Zakończono analizę rynkową")
    except Exception as e:
        logger.critical(f"Krytyczny błąd w głównej funkcji: {str(e)}")

if __name__ == "__main__":
    main()
