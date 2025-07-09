"""Interactive Brokers API integration for trading bot"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from queue import Queue

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.execution import Execution
from ibapi.common import TickerId, OrderId
from ibapi.ticktype import TickType

from config import IBConfig, AccountType
from strategies import MarketData, OrderRequest, OrderAction, OrderStatus

@dataclass
class IBPosition:
    """IB Position data"""
    account: str
    symbol: str
    position: float
    avg_cost: float
    market_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0

@dataclass
class IBOrder:
    """IB Order data"""
    order_id: int
    symbol: str
    action: str
    quantity: float
    order_type: str
    status: str
    filled: float = 0.0
    remaining: float = 0.0
    avg_fill_price: float = 0.0
    last_fill_price: float = 0.0

@dataclass
class IBExecution:
    exec_id: str
    order_id: int
    symbol: str
    side: str  # BOT or SLD
    shares: float
    price: float
    time: str
    exchange: str
    account: str
    perm_id: int

class IBKRApi(EWrapper, EClient):
    """Interactive Brokers API wrapper for trading bot"""
    
    def __init__(self, config: IBConfig, account_type):
        EClient.__init__(self, self)
        self.config = config
        self.account_type = account_type
        self.logger = logging.getLogger("IBKRApi")
        
        # Connection state
        self.is_connected = False
        self.next_order_id = None
        self.connection_event = threading.Event()
        
        # Data storage
        self.market_data: Dict[str, MarketData] = {}
        self.positions: Dict[str, IBPosition] = {}
        self.orders: Dict[int, IBOrder] = {}
        self.executions: List[IBExecution] = []
        self.account_info: Dict[str, float] = {}
        
        # Logging state tracking to prevent duplicates
        self.last_logged_order_status: Dict[int, str] = {}
        self.last_logged_open_order: Dict[int, str] = {}
        
        # Request tracking
        self.req_id_counter = 1000
        self.symbol_to_req_id: Dict[str, int] = {}
        self.req_id_to_symbol: Dict[int, str] = {}
        
        # Callbacks
        self.market_data_callbacks: List[Callable[[MarketData], None]] = []
        self.order_status_callbacks: List[Callable[[IBOrder], None]] = []
        self.position_callbacks: List[Callable[[IBPosition], None]] = []
        self.execution_callbacks: List[Callable[[IBExecution], None]] = []
        
        # Threading
        self.api_thread = None
        self.data_queue = Queue()
        
    def connect_to_ib(self, timeout=15) -> bool:
        """Connect to Interactive Brokers with configurable timeout"""
        try:
            # Clear any previous connection state
            self.connection_event.clear()
            self.is_connected = False
            
            port = self.config.get_port(self.account_type)
            self.logger.info(f"Connecting to IB at {self.config.host}:{port}")
            self.connect(self.config.host, port, self.config.client_id)
            
            # Start API thread
            self.api_thread = threading.Thread(target=self.run, daemon=True)
            self.api_thread.start()
            
            # Wait for connection with longer timeout
            if self.connection_event.wait(timeout=timeout):
                # Request delayed market data to avoid subscription errors
                self.reqMarketDataType(3)  # 3 = delayed market data
                self.logger.info("Successfully connected to IB with delayed market data")
                self.is_connected = True
                return True
            else:
                self.logger.error(f"Connection timeout - could not connect to IB within {timeout} seconds")
                # Ensure we disconnect on timeout
                try:
                    self.disconnect()
                except:
                    pass
                self.is_connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    def disconnect_from_ib(self):
        """Disconnect from Interactive Brokers and clean up resources"""
        try:
            if self.is_connected:
                self.disconnect()
            
            # Reset connection state
            self.is_connected = False
            self.next_order_id = None
            self.connection_event.clear()
            
            # Clean up data
            self.market_data.clear()
            self.positions.clear()
            self.orders.clear()
            self.account_info.clear()
            
            # Reset request tracking
            self.symbol_to_req_id.clear()
            self.req_id_to_symbol.clear()
            
            self.logger.info("Disconnected from IB and cleaned up resources")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
            # Force reset state even if disconnect fails
            self.is_connected = False
            self.connection_event.clear()
    
    # EWrapper callback methods
    def connectAck(self):
        """Called when connection is acknowledged"""
        self.logger.info("Connection acknowledged")
    
    def nextValidId(self, orderId: OrderId):
        """Called when next valid order ID is received"""
        self.next_order_id = orderId
        self.is_connected = True
        self.connection_event.set()
        self.logger.info(f"Next valid order ID: {orderId}")
    
    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        """Handle API errors with improved stability"""
        if errorCode in [2104, 2106, 2158]:  # Informational messages
            self.logger.info(f"Info {errorCode}: {errorString}")
        elif errorCode in [502, 503, 504]:  # Connection issues
            self.logger.error(f"Connection error {errorCode}: {errorString}")
            self.is_connected = False
            # Attempt graceful cleanup on connection errors
            try:
                self.disconnect()
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
        elif errorCode == 10089:  # Market data subscription error
            self.logger.warning(f"Market data error {errorCode}: {errorString} - Using delayed data")
            # Already requesting delayed data, so this is expected
        elif errorCode in [1100, 1101, 1102]:  # Connectivity issues
            self.logger.warning(f"Connectivity issue {errorCode}: {errorString}")
            self.is_connected = False
        else:
            self.logger.warning(f"Error {errorCode}: {errorString}")
    
    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib):
        """Handle price tick data"""
        symbol = self.req_id_to_symbol.get(reqId)
        if not symbol:
            return
        
        if symbol not in self.market_data:
            self.market_data[symbol] = MarketData(symbol=symbol, price=price, timestamp=datetime.now())
        
        market_data = self.market_data[symbol]
        
        # TickType constants as integers
        if tickType == 4:  # LAST price
            market_data.price = price
            market_data.timestamp = datetime.now()
        elif tickType == 1:  # BID price
            market_data.bid = price
        elif tickType == 2:  # ASK price
            market_data.ask = price
        
        # Notify callbacks
        for callback in self.market_data_callbacks:
            try:
                callback(market_data)
            except Exception as e:
                self.logger.error(f"Error in market data callback: {e}")
    
    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        """Handle size tick data"""
        symbol = self.req_id_to_symbol.get(reqId)
        if not symbol:
            return
        
        if symbol in self.market_data and tickType == 8:  # VOLUME
            self.market_data[symbol].volume = size
    
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        """Handle position updates"""
        symbol = contract.symbol
        
        ib_position = IBPosition(
            account=account,
            symbol=symbol,
            position=position,
            avg_cost=avgCost
        )
        
        self.positions[symbol] = ib_position
        
        # Notify callbacks
        for callback in self.position_callbacks:
            try:
                callback(ib_position)
            except Exception as e:
                self.logger.error(f"Error in position callback: {e}")
    
    def positionEnd(self):
        """Called when all positions have been received"""
        self.logger.info(f"Received {len(self.positions)} positions")
    
    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float,
                   avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float,
                   clientId: int, whyHeld: str, mktCapPrice: float):
        """Handle order status updates"""
        if orderId in self.orders:
            order = self.orders[orderId]
            order.status = status
            order.filled = filled
            order.remaining = remaining
            order.avg_fill_price = avgFillPrice
            order.last_fill_price = lastFillPrice
            
            # Only log if status changed or filled amount changed significantly
            status_key = f"{status}_{filled}"
            if orderId not in self.last_logged_order_status or self.last_logged_order_status[orderId] != status_key:
                self.logger.info(f"Order {orderId} status: {status}, filled: {filled}")
                self.last_logged_order_status[orderId] = status_key
            
            # Notify callbacks
            for callback in self.order_status_callbacks:
                try:
                    callback(order)
                except Exception as e:
                    self.logger.error(f"Error in order status callback: {e}")
    
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState):
        """Handle open order updates"""
        ib_order = IBOrder(
            order_id=orderId,
            symbol=contract.symbol,
            action=order.action,
            quantity=order.totalQuantity,
            order_type=order.orderType,
            status="Submitted"
        )
        
        self.orders[orderId] = ib_order
        
        # Only log if this is a new order or order details changed
        order_key = f"{contract.symbol}_{order.action}_{order.totalQuantity}"
        if orderId not in self.last_logged_open_order or self.last_logged_open_order[orderId] != order_key:
            self.logger.info(f"Open order: {orderId} {contract.symbol} {order.action} {order.totalQuantity}")
            self.last_logged_open_order[orderId] = order_key
    
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        """Handle account summary data"""
        try:
            if tag in ['TotalCashValue', 'NetLiquidation', 'AvailableFunds', 'BuyingPower']:
                self.account_info[tag] = float(value)
                self.logger.debug(f"Account {tag}: {value} {currency}")
        except ValueError:
            pass
    
    def accountSummaryEnd(self, reqId: int):
        """Called when account summary is complete"""
        self.logger.info("Account summary received")
    
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        """Handle execution details"""
        ib_execution = IBExecution(
            exec_id=execution.execId,
            order_id=execution.orderId,
            symbol=contract.symbol,
            side=execution.side,
            shares=execution.shares,
            price=execution.price,
            time=execution.time,
            exchange=execution.exchange,
            account=execution.acctNumber,
            perm_id=execution.permId
        )
        
        self.executions.append(ib_execution)
        self.logger.info(f"Execution: {execution.execId} {contract.symbol} {execution.side} {execution.shares}@{execution.price}")
        
        # Notify callbacks
        for callback in self.execution_callbacks:
            try:
                callback(ib_execution)
            except Exception as e:
                self.logger.error(f"Error in execution callback: {e}")
    
    def execDetailsEnd(self, reqId: int):
        """Called when all executions have been received"""
        self.logger.info(f"Received {len(self.executions)} executions")
    
    # Public methods for trading operations
    def create_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def subscribe_market_data(self, symbol: str) -> bool:
        """Subscribe to market data for a symbol"""
        if not self.is_connected:
            self.logger.error("Not connected to IB")
            return False
        
        try:
            req_id = self.req_id_counter
            self.req_id_counter += 1
            
            contract = self.create_stock_contract(symbol)
            
            self.symbol_to_req_id[symbol] = req_id
            self.req_id_to_symbol[req_id] = symbol
            
            # Request market data
            self.reqMktData(req_id, contract, "", False, False, [])
            
            self.logger.info(f"Subscribed to market data for {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to market data for {symbol}: {e}")
            return False
    
    def unsubscribe_market_data(self, symbol: str):
        """Unsubscribe from market data"""
        req_id = self.symbol_to_req_id.get(symbol)
        if req_id:
            self.cancelMktData(req_id)
            del self.symbol_to_req_id[symbol]
            del self.req_id_to_symbol[req_id]
            self.logger.info(f"Unsubscribed from market data for {symbol}")
    
    def place_order(self, order_request: OrderRequest) -> Optional[int]:
        """Place an order"""
        if not self.is_connected or self.next_order_id is None:
            self.logger.error("Not connected to IB or no valid order ID")
            return None
        
        try:
            order_id = self.next_order_id
            self.next_order_id += 1
            
            # Create contract
            contract = self.create_stock_contract(order_request.symbol)
            
            # Create order
            order = Order()
            order.action = order_request.action.value
            order.totalQuantity = order_request.quantity
            order.orderType = order_request.order_type

            order.eTradeOnly = False  # Disable unsupported EtradeOnly attribute
            order.firmQuoteOnly = False  # Disable unsupported FirmQuoteOnly attribute
            
            if order_request.limit_price:
                order.lmtPrice = order_request.limit_price
            if order_request.stop_price:
                order.auxPrice = order_request.stop_price
            
            # Place order
            self.placeOrder(order_id, contract, order)
            
            # Store order info
            ib_order = IBOrder(
                order_id=order_id,
                symbol=order_request.symbol,
                action=order_request.action.value,
                quantity=order_request.quantity,
                order_type=order_request.order_type,
                status="Submitted"
            )
            self.orders[order_id] = ib_order
            
            self.logger.info(f"Placed order {order_id}: {order_request.action.value} {order_request.quantity} {order_request.symbol}")
            return order_id
            
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            return None
    
    def cancel_order(self, order_id: int):
        """Cancel an order"""
        if not self.is_connected:
            self.logger.error("Not connected to IB")
            return
        
        try:
            self.cancelOrder(order_id)
            self.logger.info(f"Cancelled order {order_id}")
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
    
    def request_positions(self):
        """Request all positions"""
        if not self.is_connected:
            self.logger.error("Not connected to IB")
            return
        
        self.reqPositions()
    
    def request_account_summary(self):
        """Request account summary"""
        if not self.is_connected:
            self.logger.error("Not connected to IB")
            return
        
        tags = "TotalCashValue,NetLiquidation,AvailableFunds,BuyingPower"
        self.reqAccountSummary(9001, "All", tags)
    
    def request_account_updates(self):
        """Request account updates"""
        if not self.is_connected:
            self.logger.error("Not connected to IB")
            return
        
        # Request account summary for real-time updates
        self.request_account_summary()
        # Also request positions
        self.request_positions()
    
    def request_executions(self, days_back: int = 1):
        """Request executions from the last N days"""
        if not self.is_connected:
            self.logger.error("Not connected to IB")
            return
        
        from ibapi.execution import ExecutionFilter
        
        # Create execution filter for recent executions
        exec_filter = ExecutionFilter()
        # Get executions from the last N days
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        exec_filter.time = start_date
        
        self.reqExecutions(9002, exec_filter)
        self.logger.info(f"Requested executions from {start_date}")
    
    def get_executions(self, symbol: str = None) -> List[IBExecution]:
        """Get executions, optionally filtered by symbol"""
        if symbol:
            return [exec for exec in self.executions if exec.symbol == symbol]
        return self.executions.copy()
    
    def get_account_balance(self) -> float:
        """Get account balance"""
        return self.account_info.get('NetLiquidation', 0.0)
    
    def get_buying_power(self) -> float:
        """Get buying power"""
        return self.account_info.get('BuyingPower', 0.0)
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get latest market data for symbol"""
        return self.market_data.get(symbol)
    
    def get_position(self, symbol: str) -> Optional[IBPosition]:
        """Get position for symbol"""
        return self.positions.get(symbol)
    
    def add_market_data_callback(self, callback: Callable[[MarketData], None]):
        """Add market data callback"""
        self.market_data_callbacks.append(callback)
    
    def add_order_status_callback(self, callback: Callable[[IBOrder], None]):
        """Add order status callback"""
        self.order_status_callbacks.append(callback)
    
    def add_position_callback(self, callback: Callable[[IBPosition], None]):
        """Add position callback"""
        self.position_callbacks.append(callback)
    
    def add_execution_callback(self, callback: Callable[[IBExecution], None]):
        """Add execution callback"""
        self.execution_callbacks.append(callback)
    
    def remove_market_data_callback(self, callback: Callable[[MarketData], None]):
        """Remove market data callback"""
        if callback in self.market_data_callbacks:
            self.market_data_callbacks.remove(callback)
    
    def remove_order_status_callback(self, callback: Callable[[IBOrder], None]):
        """Remove order status callback"""
        if callback in self.order_status_callbacks:
            self.order_status_callbacks.remove(callback)
    
    def remove_position_callback(self, callback: Callable[[IBPosition], None]):
        """Remove position callback"""
        if callback in self.position_callbacks:
            self.position_callbacks.remove(callback)
    
    def remove_execution_callback(self, callback: Callable[[IBExecution], None]):
        """Remove execution callback"""
        if callback in self.execution_callbacks:
            self.execution_callbacks.remove(callback)
    
    def is_market_open(self) -> bool:
        """Check if US market is open (9:30 AM - 4:00 PM ET)"""
        try:
            import pytz
            
            # Get current time in Eastern Time
            et_tz = pytz.timezone('US/Eastern')
            now_et = datetime.now(et_tz)
            
            # Check if it's a weekday (Monday=0, Sunday=6)
            if now_et.weekday() >= 5:  # Saturday or Sunday
                return False
            
            # Market hours: 9:30 AM - 4:00 PM ET
            market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
            
            # Check if current time is within market hours
            is_open = market_open <= now_et <= market_close
            
            # TODO: Add holiday checking for more accuracy
            # For now, this covers basic market hours
            
            return is_open
            
        except ImportError:
            # Fallback if pytz is not available - use simplified UTC-based check
            self.logger.warning("pytz not available, using simplified market hours check")
            now_utc = datetime.utcnow()
            # Approximate ET as UTC-5 (ignoring DST for simplicity)
            # Market hours: 14:30 - 21:00 UTC (9:30 AM - 4:00 PM ET)
            if now_utc.weekday() >= 5:  # Weekend
                return False
            return 14 <= now_utc.hour < 21 or (now_utc.hour == 14 and now_utc.minute >= 30)
            
        except Exception as e:
            self.logger.error(f"Error checking market hours: {e}")
            # Default to market open if there's an error
            return True
    
    def check_connection_health(self, quick_check=False) -> bool:
        """Check if connection is healthy and attempt recovery if needed"""
        try:
            if not self.is_connected:
                if quick_check:
                    return False
                self.logger.warning("Connection lost, attempting to reconnect...")
                return self.connect_to_ib(timeout=20)
            
            # For quick checks, just return the connection status
            if quick_check:
                return self.is_connected
            
            # Test connection by requesting current time (only for full health checks)
            try:
                self.reqCurrentTime()
                # Wait a moment for response
                time.sleep(0.5)
                return True
            except Exception as e:
                self.logger.warning(f"Connection test failed: {e}")
                self.is_connected = False
                return self.connect_to_ib(timeout=20)
                
        except Exception as e:
            self.logger.error(f"Connection health check failed: {e}")
            self.is_connected = False
            if quick_check:
                return False
            return self.connect_to_ib(timeout=20)
    
    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """Wait for connection to be established"""
        return self.connection_event.wait(timeout)


# Global API instance
_api_instance = None

def get_api_instance() -> Optional[IBKRApi]:
    """Get the global API instance"""
    global _api_instance
    return _api_instance

def set_api_instance(api: IBKRApi) -> None:
    """Set the global API instance"""
    global _api_instance
    _api_instance = api