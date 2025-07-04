from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData, TickType
import threading
import time
from datetime import datetime

class AdvancedIBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.historical_data = {}
        self.real_time_data = {}
        self.requests_completed = set()
        
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"Error {errorCode} for request {reqId}: {errorString}")
        
    def historicalData(self, reqId, bar: BarData):
        """Callback for historical data"""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
        
    def historicalDataEnd(self, reqId, start, end):
        """Called when historical data request is complete"""
        data_count = len(self.historical_data.get(reqId, []))
        print(f"Request {reqId} complete: Received {data_count} historical bars")
        self.requests_completed.add(reqId)
        
    def tickPrice(self, reqId, tickType, price, attrib):
        """Real-time price updates"""
        tick_name = TickType.to_str(tickType)
        print(f"Real-time {tick_name}: ${price:.2f}")
        
        if reqId not in self.real_time_data:
            self.real_time_data[reqId] = {}
        self.real_time_data[reqId][tick_name] = price
        
    def tickSize(self, reqId, tickType, size):
        """Real-time size updates"""
        tick_name = TickType.to_str(tickType)
        if 'Volume' in tick_name or 'Size' in tick_name:
            print(f"Real-time {tick_name}: {size}")
        
    def nextValidId(self, orderId):
        """Called when connection is established"""
        print(f"Connected! Next valid order ID: {orderId}")
        self.start_requests()
        
    def create_stock_contract(self, symbol, exchange="SMART", currency="USD"):
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract
        
    def create_forex_contract(self, symbol):
        """Create a forex contract (e.g., 'EURUSD')"""
        contract = Contract()
        contract.symbol = symbol[:3]  # Base currency
        contract.secType = "CASH"
        contract.currency = symbol[3:]  # Quote currency
        contract.exchange = "IDEALPRO"
        return contract
        
    def create_crypto_contract(self, symbol):
        """Create a crypto contract (e.g., 'BTCUSD')"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "CRYPTO"
        contract.exchange = "PAXOS"
        contract.currency = "USD"
        return contract
        
    def start_requests(self):
        """Start various data requests"""
        end_date = datetime.now().strftime("%Y%m%d %H:%M:%S")
        
        # 1. Stock historical data - Apple
        print("\n1. Requesting AAPL historical data...")
        aapl_contract = self.create_stock_contract("AAPL")
        self.reqHistoricalData(
            reqId=1,
            contract=aapl_contract,
            endDateTime=end_date,
            durationStr="5 D",
            barSizeSetting="1 hour",
            whatToShow="TRADES",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )
        
        # 2. Different stock with minute data - Microsoft
        print("\n2. Requesting MSFT minute data...")
        msft_contract = self.create_stock_contract("MSFT")
        self.reqHistoricalData(
            reqId=2,
            contract=msft_contract,
            endDateTime=end_date,
            durationStr="1 D",
            barSizeSetting="5 mins",
            whatToShow="TRADES",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )
        
        # 3. Forex data - EUR/USD
        print("\n3. Requesting EURUSD forex data...")
        eur_contract = self.create_forex_contract("EURUSD")
        self.reqHistoricalData(
            reqId=3,
            contract=eur_contract,
            endDateTime=end_date,
            durationStr="1 W",
            barSizeSetting="1 hour",
            whatToShow="MIDPOINT",
            useRTH=0,  # 24/7 for forex
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )
        
        # 4. Real-time data for Apple (uncomment to enable)
        # print("\n4. Starting real-time data for AAPL...")
        # self.reqMktData(reqId=100, contract=aapl_contract, genericTickList="", snapshot=False, regulatorySnapshot=False, mktDataOptions=[])
        
    def print_summary(self):
        """Print summary of received data"""
        print("\n" + "="*50)
        print("DATA SUMMARY")
        print("="*50)
        
        for req_id, data in self.historical_data.items():
            print(f"\nRequest {req_id}: {len(data)} data points")
            if data:
                print(f"  First: {data[0]['date']} - Close: ${data[0]['close']:.2f}")
                print(f"  Last:  {data[-1]['date']} - Close: ${data[-1]['close']:.2f}")
                
        if self.real_time_data:
            print(f"\nReal-time data received for {len(self.real_time_data)} instruments")

def main():
    print("Advanced Interactive Brokers API Examples")
    print("Make sure TWS or IB Gateway is running with API enabled!")
    
    app = AdvancedIBApi()
    app.connect("127.0.0.1", 7497, clientId=2)
    
    # Start the socket in a thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    
    # Wait for all historical data requests to complete
    expected_requests = {1, 2, 3}  # Request IDs we're expecting
    timeout = 60  # 60 seconds timeout
    start_time = time.time()
    
    while (not expected_requests.issubset(app.requests_completed) and 
           (time.time() - start_time) < timeout):
        time.sleep(1)
    
    if expected_requests.issubset(app.requests_completed):
        print("\nAll historical data requests completed!")
        app.print_summary()
    else:
        print("\nTimeout: Not all data received. Check your connection and permissions.")
        print(f"Completed requests: {app.requests_completed}")
    
    # Keep running for a bit to see real-time data (if enabled)
    print("\nWaiting 10 seconds for any real-time data...")
    time.sleep(10)
    
    app.disconnect()
    print("\nDisconnected from TWS/Gateway")

if __name__ == "__main__":
    main()