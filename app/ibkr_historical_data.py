"""Interactive Brokers Historical Data Module for Backtesting"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import logging
import threading
import time
from dataclasses import dataclass

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData

from config import IBConfig, AccountType

@dataclass
class HistoricalBar:
    """Structured historical data point"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    @classmethod
    def from_bar_data(cls, bar: BarData) -> 'HistoricalBar':
        return cls(
            date=bar.date,
            open=float(bar.open),
            high=float(bar.high),
            low=float(bar.low),
            close=float(bar.close),
            volume=int(float(bar.volume))  # Handle fractional volumes
        )

class IBKRHistoricalDataClient(EWrapper, EClient):
    """IBKR client specifically for historical data retrieval"""
    
    def __init__(self, config: IBConfig, account_type: AccountType):
        EClient.__init__(self, self)
        self.config = config
        self.account_type = account_type
        self.logger = logging.getLogger("IBKRHistoricalData")
        
        # Connection state
        self.is_connected = False
        self.connection_event = threading.Event()
        self.api_thread = None
        
        # Data storage
        self.historical_data: Dict[int, List[HistoricalBar]] = {}
        self.requests_completed: set = set()
        self.request_errors: Dict[int, str] = {}
        
        # Request tracking
        self.req_id_counter = 1000
        
    def connect_to_ib(self, timeout: int = 30) -> bool:
        """Connect to Interactive Brokers"""
        try:
            self.connection_event.clear()
            self.is_connected = False
            
            port = self.config.get_port(self.account_type)
            self.logger.info(f"Connecting to IB at {self.config.host}:{port} for historical data")
            self.connect(self.config.host, port, self.config.client_id + 100)  # Use different client ID
            
            # Start API thread
            self.api_thread = threading.Thread(target=self.run, daemon=True)
            self.api_thread.start()
            
            # Wait for connection
            if self.connection_event.wait(timeout=timeout):
                self.logger.info("Successfully connected to IB for historical data")
                self.is_connected = True
                return True
            else:
                self.logger.error(f"Connection timeout - could not connect to IB within {timeout} seconds")
                self.is_connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    def disconnect_from_ib(self):
        """Disconnect from Interactive Brokers"""
        try:
            if self.is_connected:
                self.disconnect()
            self.is_connected = False
            self.connection_event.clear()
            self.logger.info("Disconnected from IB historical data client")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    # EWrapper callback methods
    def nextValidId(self, orderId: int):
        """Called when connection is established"""
        self.logger.info(f"Historical data client connected! Next valid order ID: {orderId}")
        self.is_connected = True
        self.connection_event.set()
    
    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
        """Handle API errors"""
        if errorCode in [2104, 2106, 2107, 2158]:  # Info messages
            self.logger.info(f"IB Info {errorCode}: {errorString}")
        elif errorCode in [2174, 2176]:  # Warnings
            self.logger.warning(f"IB Warning {errorCode}: {errorString}")
        elif errorCode >= 500:  # Critical errors
            self.logger.error(f"CRITICAL ERROR {errorCode} for request {reqId}: {errorString}")
            self.request_errors[reqId] = f"Error {errorCode}: {errorString}"
            self.requests_completed.add(reqId)
        else:
            self.logger.error(f"IB Error {errorCode} for request {reqId}: {errorString}")
            if reqId != -1:  # Only mark specific requests as failed
                self.request_errors[reqId] = f"Error {errorCode}: {errorString}"
                self.requests_completed.add(reqId)
    
    def historicalData(self, reqId: int, bar: BarData):
        """Process incoming historical data"""
        try:
            if reqId not in self.historical_data:
                self.historical_data[reqId] = []
            
            historical_bar = HistoricalBar.from_bar_data(bar)
            self.historical_data[reqId].append(historical_bar)
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error processing bar data for request {reqId}: {e}")
    
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """Called when historical data request is complete"""
        data_count = len(self.historical_data.get(reqId, []))
        self.logger.info(f"Historical data request {reqId} complete: Received {data_count} bars")
        self.requests_completed.add(reqId)
    
    def create_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def get_ibkr_bar_size(self, interval: str) -> str:
        """Convert interval format to IBKR bar size format"""
        interval_mapping = {
            "1m": "1 min",
            "5m": "5 mins",
            "15m": "15 mins",
            "30m": "30 mins",
            "1h": "1 hour",
            "2h": "2 hours",
            "4h": "4 hours",
            "1d": "1 day",
            "1w": "1 week",
            "1M": "1 month"
        }
        return interval_mapping.get(interval, "1 hour")
    
    def calculate_duration(self, start_date: str, end_date: str, interval: str) -> str:
        """Calculate duration string for IBKR based on date range and interval"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end_dt - start_dt).days
        
        # IBKR actual limitations based on their API documentation:
        # - 1-5 min bars: up to 180 days
        # - 15-30 min bars: up to 2 years
        # - 1 hour bars: up to 2 years
        # - Daily bars: up to 10+ years
        
        if interval in ['1m', '5m']:
            # 1-5 minute data: up to 180 days
            if days_diff <= 180:
                return f"{days_diff} D"
            else:
                return "180 D"
        elif interval in ['15m', '30m', '1h', '2h', '4h']:
            # 15min-4hour data: up to 2 years
            if days_diff <= 730:  # ~2 years
                return f"{days_diff} D"
            else:
                return "2 Y"
        else:
            # Daily and above: up to 10 years
            if days_diff <= 3650:  # ~10 years
                return f"{days_diff} D"
            else:
                return "10 Y"
    
    def fetch_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = '1h') -> pd.DataFrame:
        """Fetch historical data from IBKR and return as pandas DataFrame"""
        if not self.is_connected:
            raise ConnectionError("Not connected to IBKR")
        
        try:
            req_id = self.req_id_counter
            self.req_id_counter += 1
            
            # Create contract
            contract = self.create_stock_contract(symbol)
            
            # Convert parameters
            bar_size = self.get_ibkr_bar_size(interval)
            duration = self.calculate_duration(start_date, end_date, interval)
            
            # Use end_date as the end time
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_datetime = end_dt.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            end_date_str = end_datetime.strftime("%Y%m%d %H:%M:%S UTC")
            
            self.logger.info(f"Requesting historical data for {symbol}: {duration}, {bar_size}")
            
            # Clear previous data for this request
            if req_id in self.historical_data:
                del self.historical_data[req_id]
            if req_id in self.request_errors:
                del self.request_errors[req_id]
            
            # Request historical data
            self.reqHistoricalData(
                reqId=req_id,
                contract=contract,
                endDateTime=end_date_str,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=1,  # Regular trading hours only
                formatDate=1,  # Format as string
                keepUpToDate=False,
                chartOptions=[]
            )
            
            # Wait for data to be received
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while (req_id not in self.requests_completed and 
                   (time.time() - start_time) < timeout):
                time.sleep(0.1)
            
            # Check for errors
            if req_id in self.request_errors:
                raise Exception(f"IBKR API Error: {self.request_errors[req_id]}")
            
            # Check if we received data
            if req_id not in self.historical_data or not self.historical_data[req_id]:
                raise Exception(f"No historical data received for {symbol}")
            
            # Convert to pandas DataFrame
            data = self.historical_data[req_id]
            df_data = []
            
            for bar in data:
                # Parse the date string to datetime
                try:
                    # IBKR returns dates in format "20231201 16:00:00" or "20231201"
                    if ' ' in bar.date:
                        dt = datetime.strptime(bar.date, "%Y%m%d %H:%M:%S")
                    else:
                        dt = datetime.strptime(bar.date, "%Y%m%d")
                except ValueError:
                    # Try alternative format
                    dt = datetime.strptime(bar.date, "%Y%m%d")
                
                df_data.append({
                    'Open': bar.open,
                    'High': bar.high,
                    'Low': bar.low,
                    'Close': bar.close,
                    'Volume': bar.volume
                })
            
            # Create DataFrame with datetime index
            df = pd.DataFrame(df_data)
            
            # Create datetime index from the parsed dates
            dates = []
            for bar in data:
                try:
                    if ' ' in bar.date:
                        dt = datetime.strptime(bar.date, "%Y%m%d %H:%M:%S")
                    else:
                        dt = datetime.strptime(bar.date, "%Y%m%d")
                    dates.append(dt)
                except ValueError:
                    dt = datetime.strptime(bar.date, "%Y%m%d")
                    dates.append(dt)
            
            df.index = pd.DatetimeIndex(dates)
            df.index.name = 'Datetime'
            
            # Sort by date to ensure chronological order
            df = df.sort_index()
            
            self.logger.info(f"Successfully retrieved {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            raise

class IBKRDataProvider:
    """High-level interface for IBKR historical data"""
    
    def __init__(self, config: IBConfig, account_type: AccountType):
        self.config = config
        self.account_type = account_type
        self.logger = logging.getLogger("IBKRDataProvider")
        self.client = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def connect(self) -> bool:
        """Connect to IBKR"""
        try:
            self.client = IBKRHistoricalDataClient(self.config, self.account_type)
            return self.client.connect_to_ib()
        except Exception as e:
            self.logger.error(f"Failed to connect IBKR data provider: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.client:
            self.client.disconnect_from_ib()
            self.client = None
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str, interval: str = '1h') -> pd.DataFrame:
        """Fetch historical data"""
        if not self.client or not self.client.is_connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        return self.client.fetch_historical_data(symbol, start_date, end_date, interval)

# Utility function for easy integration
def fetch_ibkr_data(symbol: str, start_date: str, end_date: str, interval: str = '1h', 
                   config: IBConfig = None, account_type: AccountType = AccountType.DEMO) -> pd.DataFrame:
    """Convenience function to fetch IBKR historical data"""
    if config is None:
        config = IBConfig()
    
    with IBKRDataProvider(config, account_type) as provider:
        return provider.fetch_data(symbol, start_date, end_date, interval)