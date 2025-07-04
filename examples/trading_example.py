from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import BarData
import threading
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_api.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class Position:
    """Represents a trading position"""
    account: str
    symbol: str
    position: float
    market_price: float
    market_value: float
    average_cost: float
    unrealized_pnl: float
    realized_pnl: float

@dataclass
class OrderStatus:
    """Represents order status information"""
    order_id: int
    status: str
    filled: float
    remaining: float
    avg_fill_price: float
    perm_id: int
    parent_id: int
    last_fill_price: float
    client_id: int
    why_held: str
    mkt_cap_price: float

class Config:
    """Trading configuration settings"""
    HOST = "127.0.0.1"
    PORT = 4001  # IB Gateway paper trading
    CLIENT_ID = 1
    TIMEOUT = 30

class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.logger = logging.getLogger(__name__)
        self.next_order_id = None
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[int, OrderStatus] = {}
        self.connected = False
        
    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:
        """Enhanced error handling"""
        if errorCode in [2104, 2106, 2107, 2158]:  # Info messages
            self.logger.info(f"IB Status {errorCode}: {errorString}")
        elif errorCode in [2174, 2176]:  # Warnings
            self.logger.warning(f"IB Warning {errorCode}: {errorString}")
        elif errorCode >= 500:  # Critical errors
            self.logger.error(f"CRITICAL ERROR {errorCode}: {errorString}")
        else:
            self.logger.error(f"IB Error {errorCode}: {errorString}")
    
    def nextValidId(self, orderId: int) -> None:
        """Called when connection is established"""
        self.logger.info(f"Connected! Next valid order ID: {orderId}")
        self.next_order_id = orderId
        self.connected = True
        
        # Request account updates and positions
        self.reqAccountUpdates(True, "")  # Subscribe to account updates
        self.reqPositions()  # Request current positions
    
    def position(self, account: str, contract: Contract, position: float, avgCost: float) -> None:
        """Called for each position"""
        if position != 0:  # Only show non-zero positions
            key = f"{contract.symbol}_{contract.secType}"
            # We'll update market value when we get the price update
            pos = Position(
                account=account,
                symbol=contract.symbol,
                position=position,
                market_price=0.0,  # Will be updated
                market_value=0.0,  # Will be calculated
                average_cost=avgCost,
                unrealized_pnl=0.0,  # Will be updated
                realized_pnl=0.0   # Will be updated
            )
            self.positions[key] = pos
            self.logger.info(f"Position: {contract.symbol} - Qty: {position}, Avg Cost: ${avgCost:.2f}")
    
    def positionEnd(self) -> None:
        """Called when all positions have been received"""
        self.logger.info("All positions received")
        self.display_positions()
    
    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str) -> None:
        """Called for account value updates"""
        if key in ['TotalCashValue', 'NetLiquidation', 'UnrealizedPnL', 'RealizedPnL']:
            self.logger.info(f"Account {key}: {val} {currency}")
    
    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float,
                   avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float,
                   clientId: int, whyHeld: str, mktCapPrice: float) -> None:
        """Called when order status changes"""
        order_status = OrderStatus(
            order_id=orderId,
            status=status,
            filled=filled,
            remaining=remaining,
            avg_fill_price=avgFillPrice,
            perm_id=permId,
            parent_id=parentId,
            last_fill_price=lastFillPrice,
            client_id=clientId,
            why_held=whyHeld,
            mkt_cap_price=mktCapPrice
        )
        self.orders[orderId] = order_status
        
        self.logger.info(f"Order {orderId}: {status} - Filled: {filled}, Remaining: {remaining}")
        if avgFillPrice > 0:
            self.logger.info(f"Average Fill Price: ${avgFillPrice:.2f}")
    
    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState) -> None:
        """Called for open orders"""
        self.logger.info(f"Open Order {orderId}: {order.action} {order.totalQuantity} {contract.symbol} @ {order.orderType}")
    
    def create_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def create_market_order(self, action: str, quantity: int) -> Order:
        """Create a market order"""
        order = Order()
        order.action = action  # "BUY" or "SELL"
        order.orderType = "MKT"  # Market order
        order.totalQuantity = quantity
        return order
    
    def create_limit_order(self, action: str, quantity: int, limit_price: float) -> Order:
        """Create a limit order"""
        order = Order()
        order.action = action  # "BUY" or "SELL"
        order.orderType = "LMT"  # Limit order
        order.totalQuantity = quantity
        order.lmtPrice = limit_price
        return order
    
    def place_buy_order(self, symbol: str, quantity: int, order_type: str = "MKT", limit_price: float = None) -> int:
        """Place a buy order"""
        if not self.connected or self.next_order_id is None:
            self.logger.error("Not connected or no valid order ID")
            return None
        
        # Create contract
        contract = self.create_stock_contract(symbol)
        
        # Create order
        if order_type == "MKT":
            order = self.create_market_order("BUY", quantity)
        elif order_type == "LMT" and limit_price is not None:
            order = self.create_limit_order("BUY", quantity, limit_price)
        else:
            self.logger.error("Invalid order type or missing limit price")
            return None
        
        # Place order
        order_id = self.next_order_id
        self.placeOrder(order_id, contract, order)
        self.next_order_id += 1
        
        self.logger.info(f"Placed {order_type} BUY order for {quantity} shares of {symbol} (Order ID: {order_id})")
        if limit_price:
            self.logger.info(f"Limit Price: ${limit_price:.2f}")
        
        return order_id
    
    def place_sell_order(self, symbol: str, quantity: int, order_type: str = "MKT", limit_price: float = None) -> int:
        """Place a sell order"""
        if not self.connected or self.next_order_id is None:
            self.logger.error("Not connected or no valid order ID")
            return None
        
        # Create contract
        contract = self.create_stock_contract(symbol)
        
        # Create order
        if order_type == "MKT":
            order = self.create_market_order("SELL", quantity)
        elif order_type == "LMT" and limit_price is not None:
            order = self.create_limit_order("SELL", quantity, limit_price)
        else:
            self.logger.error("Invalid order type or missing limit price")
            return None
        
        # Place order
        order_id = self.next_order_id
        self.placeOrder(order_id, contract, order)
        self.next_order_id += 1
        
        self.logger.info(f"Placed {order_type} SELL order for {quantity} shares of {symbol} (Order ID: {order_id})")
        if limit_price:
            self.logger.info(f"Limit Price: ${limit_price:.2f}")
        
        return order_id
    
    def cancel_order(self, order_id: int) -> None:
        """Cancel an order"""
        self.cancelOrder(order_id)
        self.logger.info(f"Cancelled order {order_id}")
    
    def display_positions(self) -> None:
        """Display current positions"""
        if not self.positions:
            print("\n=== NO POSITIONS ===")
            return
        
        print("\n=== CURRENT POSITIONS ===")
        print(f"{'Symbol':<10} {'Quantity':<10} {'Avg Cost':<12} {'Market Value':<15} {'P&L':<12}")
        print("-" * 70)
        
        for key, pos in self.positions.items():
            pnl = (pos.market_price - pos.average_cost) * pos.position if pos.market_price > 0 else 0
            market_val = pos.market_price * pos.position if pos.market_price > 0 else 0
            
            print(f"{pos.symbol:<10} {pos.position:<10.0f} ${pos.average_cost:<11.2f} ${market_val:<14.2f} ${pnl:<11.2f}")
    
    def display_orders(self) -> None:
        """Display order status"""
        if not self.orders:
            print("\n=== NO ORDERS ===")
            return
        
        print("\n=== ORDER STATUS ===")
        print(f"{'Order ID':<10} {'Status':<12} {'Filled':<8} {'Remaining':<10} {'Avg Price':<12}")
        print("-" * 65)
        
        for order_id, order in self.orders.items():
            avg_price = f"${order.avg_fill_price:.2f}" if order.avg_fill_price > 0 else "N/A"
            print(f"{order_id:<10} {order.status:<12} {order.filled:<8.0f} {order.remaining:<10.0f} {avg_price:<12}")

def main() -> None:
    """Main trading function"""
    logger = logging.getLogger(__name__)
    logger.info("Starting Interactive Brokers Trading API...")
    logger.info("Make sure TWS or IB Gateway is running and API is enabled!")
    
    # Create trading app instance
    app = TradingApp()
    
    try:
        # Connect to TWS/Gateway
        app.connect(Config.HOST, Config.PORT, Config.CLIENT_ID)
        logger.info(f"Connecting to {Config.HOST}:{Config.PORT} with client ID {Config.CLIENT_ID}")
        
        # Start the socket in a thread
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not app.connected and (time.time() - start_time) < timeout:
            time.sleep(0.5)
        
        if not app.connected:
            logger.error("Failed to connect to TWS/Gateway")
            return
        
        # Wait a moment for initial data
        time.sleep(3)
        
        # Example trading operations
        print("\n" + "="*50)
        print("INTERACTIVE BROKERS TRADING EXAMPLE")
        print("="*50)
        
        # Display current positions
        app.display_positions()
        
        # Example: Place a buy order for Apple stock
        print("\n=== PLACING SAMPLE ORDERS ===")
        
        # Market buy order
        order_id1 = app.place_buy_order("AAPL", 10, "MKT")
        
        # Limit buy order
        order_id2 = app.place_buy_order("MSFT", 5, "LMT", 300.00)
        
        # Wait for order updates
        time.sleep(5)
        
        # Display order status
        app.display_orders()
        
        # Example: Cancel the limit order if it's still pending
        if order_id2 and order_id2 in app.orders:
            if app.orders[order_id2].status in ['PreSubmitted', 'Submitted']:
                print(f"\nCancelling pending limit order {order_id2}...")
                app.cancel_order(order_id2)
                time.sleep(2)
        
        # Final status check
        time.sleep(3)
        app.display_positions()
        app.display_orders()
        
        print("\n=== TRADING SESSION COMPLETE ===")
        print("Check the 'trading_api.log' file for detailed logs.")
        
    except Exception as e:
        logger.error(f"Trading error: {e}")
        print(f"Trading error: {e}")
    
    finally:
        # Disconnect
        app.disconnect()
        logger.info("Disconnected from TWS/Gateway")
        print("\nDisconnected from TWS/Gateway")

if __name__ == "__main__":
    main()