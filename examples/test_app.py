from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData
import threading
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ib_api.log'),
        logging.StreamHandler()
    ]
)

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

class Config:
    """Configuration settings"""
    HOST = "127.0.0.1"
    PORT = 4001  # IB Gateway paper trading
    CLIENT_ID = 1
    TIMEOUT = 30
    
    # Data request settings
    DURATION = "30 D"
    BAR_SIZE = "1 day"
    DATA_TYPE = "TRADES"

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.logger = logging.getLogger(__name__)
        self.data: List[HistoricalBar] = []
        self.data_received: bool = False
        
    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:
        """Enhanced error handling with categorization"""
        if errorCode in [2104, 2106, 2107, 2158]:  # Info messages
            self.logger.info(f"IB Status {errorCode}: {errorString}")
        elif errorCode in [2174, 2176]:  # Warnings
            self.logger.warning(f"IB Warning {errorCode}: {errorString}")
        elif errorCode >= 500:  # Critical errors
            self.logger.error(f"CRITICAL ERROR {errorCode}: {errorString}")
            self.data_received = True  # Stop waiting on critical errors
        else:
            self.logger.error(f"IB Error {errorCode}: {errorString}")
        
    def historicalData(self, reqId: int, bar: BarData) -> None:
        """Process incoming historical data with validation"""
        try:
            historical_bar = HistoricalBar.from_bar_data(bar)
            self.data.append(historical_bar)
            self.logger.info(f"Received: {historical_bar.date} - Close: {historical_bar.close}")
        except (ValueError, TypeError) as e:
            self.logger.error(f"Error processing bar data: {e}")
        
    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        """Called when historical data request is complete"""
        self.logger.info(f"Historical data request complete. Received {len(self.data)} bars.")
        self.data_received = True
        
    def nextValidId(self, orderId: int) -> None:
        """Called when connection is established"""
        self.logger.info(f"Connected! Next valid order ID: {orderId}")
        self.start_requests()
        
    def start_requests(self) -> None:
        """Start requesting historical data after connection"""
        # Create contract for Apple stock
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        # Use explicit timezone (UTC) to avoid warning 2174
        end_date = datetime.now(timezone.utc).strftime("%Y%m%d %H:%M:%S UTC")
        
        self.logger.info("Requesting historical data for AAPL...")
        self.reqHistoricalData(
            reqId=1,
            contract=contract,
            endDateTime=end_date,  # Now with explicit timezone
            durationStr=Config.DURATION,
            barSizeSetting=Config.BAR_SIZE,
            whatToShow=Config.DATA_TYPE,
            useRTH=1,  # Regular trading hours only
            formatDate=1,  # Format as string
            keepUpToDate=False,
            chartOptions=[]
        )

def main() -> None:
    """Main function with enhanced error handling and logging"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Interactive Brokers API connection...")
    logger.info("Make sure TWS or IB Gateway is running and API is enabled!")
    
    # Create API instance
    app = IBApi()
    
    try:
        # Connect to TWS/Gateway using configuration
        app.connect(Config.HOST, Config.PORT, Config.CLIENT_ID)
        logger.info(f"Connecting to {Config.HOST}:{Config.PORT} with client ID {Config.CLIENT_ID}")
        
        # Start the socket in a thread
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        # Allow connection to establish
        time.sleep(2)
        
        # Wait for data to be received
        start_time = time.time()
        
        while not app.data_received and (time.time() - start_time) < Config.TIMEOUT:
            time.sleep(1)
        
        if app.data_received:
            logger.info(f"Successfully received {len(app.data)} historical data points!")
            print(f"\n=== RESULTS ===")
            print(f"Successfully received {len(app.data)} historical data points!")
            print("\nFirst 5 data points:")
            for i, bar in enumerate(app.data[:5]):
                print(f"{i+1}. Date: {bar.date}, Close: ${bar.close:.2f}, Volume: {bar.volume:,}")
        else:
            logger.warning("Timeout: No data received. Check your TWS/Gateway connection.")
            print("\nTimeout: No data received. Check your TWS/Gateway connection.")
    
    except Exception as e:
        logger.error(f"Connection error: {e}")
        print(f"Connection error: {e}")
    
    finally:
        # Disconnect
        app.disconnect()
        logger.info("Disconnected from TWS/Gateway")
        print("Disconnected from TWS/Gateway")

if __name__ == "__main__":
    main()