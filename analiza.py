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
            self.data['RSI_High'] = 65 + (self.data
