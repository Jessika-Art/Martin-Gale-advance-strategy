#!/usr/bin/env python3
"""
Clean Trading Example - Interactive Brokers API
Demonstrates how to place trades and view positions

IMPORTANT: This connects to paper trading (port 4001) by default.
Make sure IB Gateway is running with API enabled.
"""

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clean_trading.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class Position:
    """Simple position data structure"""
    symbol: str
    position: float
    avg_cost: float
    market_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.position * self.market_price
    
    @property
    def unrealized_pnl(self) -> float:
        return (self.market_price - self.avg_cost) * self.position

@dataclass
class OrderInfo:
    """Simple order information"""
    order_id: int
    symbol: str
    action: str
    quantity: int
    order_type: str
    status: str = "Unknown"
    filled: float = 0.0
    remaining: float = 0.0
    avg_price: float = 0.0

class CleanTradingApp(EWrapper, EClient):
    """Clean trading application without special characters"""
    
    def __init__(self):
        EClient.__init__(self, self)
        self.logger = logging.getLogger(__name__)
        
        # Data storage
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[int, OrderInfo] = {}
        self.next_order_id: Optional[int] = None
        self.connected = False
        
        # Events
        self.position_event = threading.Event()
        self.order_event = threading.Event()
    
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """Handle API errors"""
        if errorCode in [2104, 2106, 2158]:  # Info messages
            self.logger.info(f"INFO {errorCode}: {errorString}")
        elif errorCode in [2174, 2176]:  # Warnings
            self.logger.warning(f"WARNING {errorCode}: {errorString}")
        elif errorCode >= 10000:  # Critical errors
            self.logger.error(f"CRITICAL ERROR {errorCode}: {errorString}")
        else:
            self.logger.error(f"ERROR {errorCode}: {errorString}")
    
    def nextValidId(self, orderId: int):
        """Receive next valid order ID"""
        self.next_order_id = orderId
        self.logger.info(f"Next valid order ID: {orderId}")
    
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        """Receive position data"""
        if position != 0:  # Only store non-zero positions
            key = f"{contract.symbol}_{contract.secType}"
            self.positions[key] = Position(
                symbol=contract.symbol,
                position=position,
                avg_cost=avgCost
            )
            self.logger.info(f"Position: {contract.symbol} - {position} shares @ ${avgCost:.2f}")
    
    def positionEnd(self):
        """Called when all positions have been received"""
        self.logger.info("Position data complete")
        self.position_event.set()
    
    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float, 
                   avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, 
                   clientId: int, whyHeld: str, mktCapPrice: float):
        """Receive order status updates"""
        if orderId in self.orders:
            order_info = self.orders[orderId]
            order_info.status = status
            order_info.filled = filled
            order_info.remaining = remaining
            order_info.avg_price = avgFillPrice
            
            self.logger.info(f"Order {orderId} ({order_info.symbol}): {status} - Filled: {filled}, Remaining: {remaining}")
            
            if status in ["Filled", "Cancelled", "Rejected"]:
                self.order_event.set()
    
    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState):
        """Receive open order information"""
        if orderId not in self.orders:
            self.orders[orderId] = OrderInfo(
                order_id=orderId,
                symbol=contract.symbol,
                action=order.action,
                quantity=int(order.totalQuantity),
                order_type=order.orderType
            )
    
    def create_stock_contract(self, symbol: str) -> Contract:
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract
    
    def create_market_order(self, action: str, quantity: int) -> Order:
        """Create a simple market order"""
        order = Order()
        order.action = action
        order.orderType = "MKT"
        order.totalQuantity = quantity
        return order
    
    def create_limit_order(self, action: str, quantity: int, limit_price: float) -> Order:
        """Create a simple limit order"""
        order = Order()
        order.action = action
        order.orderType = "LMT"
        order.totalQuantity = quantity
        order.lmtPrice = limit_price
        return order
    
    def place_buy_order(self, symbol: str, quantity: int, order_type: str = "MKT", limit_price: float = None) -> Optional[int]:
        """Place a buy order"""
        if not self.connected or self.next_order_id is None:
            self.logger.error("Not connected or no valid order ID")
            return None
        
        try:
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
            
            # Store order info
            order_id = self.next_order_id
            self.orders[order_id] = OrderInfo(
                order_id=order_id,
                symbol=symbol,
                action="BUY",
                quantity=quantity,
                order_type=order_type
            )
            
            # Place order
            self.placeOrder(order_id, contract, order)
            self.next_order_id += 1
            
            print(f"[SUCCESS] Placed {order_type} BUY order for {quantity} shares of {symbol} (Order ID: {order_id})")
            if limit_price:
                print(f"[INFO] Limit Price: ${limit_price:.2f}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"Error placing buy order: {e}")
            return None
    
    def place_sell_order(self, symbol: str, quantity: int, order_type: str = "MKT", limit_price: float = None) -> Optional[int]:
        """Place a sell order"""
        if not self.connected or self.next_order_id is None:
            self.logger.error("Not connected or no valid order ID")
            return None
        
        try:
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
            
            # Store order info
            order_id = self.next_order_id
            self.orders[order_id] = OrderInfo(
                order_id=order_id,
                symbol=symbol,
                action="SELL",
                quantity=quantity,
                order_type=order_type
            )
            
            # Place order
            self.placeOrder(order_id, contract, order)
            self.next_order_id += 1
            
            print(f"[SUCCESS] Placed {order_type} SELL order for {quantity} shares of {symbol} (Order ID: {order_id})")
            if limit_price:
                print(f"[INFO] Limit Price: ${limit_price:.2f}")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"Error placing sell order: {e}")
            return None
    
    def cancel_order(self, order_id: int):
        """Cancel an order"""
        try:
            self.cancelOrder(order_id, "")
            print(f"[CANCELLED] Order {order_id} cancelled")
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
    
    def display_positions(self):
        """Display current positions"""
        print("\n" + "="*60)
        print("CURRENT POSITIONS")
        print("="*60)
        
        if not self.positions:
            print("No positions found")
            return
        
        print(f"{'Symbol':<8} {'Quantity':<10} {'Avg Cost':<12} {'Market Value':<15} {'P&L':<12}")
        print("-" * 60)
        
        total_value = 0
        total_pnl = 0
        
        for key, pos in self.positions.items():
            market_value = pos.market_value if pos.market_price > 0 else pos.position * pos.avg_cost
            pnl = pos.unrealized_pnl if pos.market_price > 0 else 0
            
            print(f"{pos.symbol:<8} {pos.position:<10.0f} ${pos.avg_cost:<11.2f} ${market_value:<14.2f} ${pnl:<11.2f}")
            
            total_value += market_value
            total_pnl += pnl
        
        print("-" * 60)
        print(f"{'TOTAL':<8} {'':<10} {'':<12} ${total_value:<14.2f} ${total_pnl:<11.2f}")
    
    def display_orders(self):
        """Display current orders"""
        print("\n" + "="*70)
        print("CURRENT ORDERS")
        print("="*70)
        
        if not self.orders:
            print("No orders found")
            return
        
        print(f"{'ID':<5} {'Symbol':<8} {'Action':<6} {'Qty':<5} {'Type':<5} {'Status':<12} {'Filled':<8} {'Avg Price':<10}")
        print("-" * 70)
        
        for order_id, order_info in self.orders.items():
            avg_price_str = f"${order_info.avg_price:.2f}" if order_info.avg_price > 0 else "N/A"
            print(f"{order_id:<5} {order_info.symbol:<8} {order_info.action:<6} {order_info.quantity:<5} "
                  f"{order_info.order_type:<5} {order_info.status:<12} {order_info.filled:<8.0f} {avg_price_str:<10}")
    
    def connect_and_run(self, host: str = "127.0.0.1", port: int = 4001, client_id: int = 1):
        """Connect to TWS/Gateway and start the API"""
        try:
            print(f"[CONNECTING] Connecting to {host}:{port} (Client ID: {client_id})")
            self.connect(host, port, client_id)
            
            # Start the API thread
            api_thread = threading.Thread(target=self.run, daemon=True)
            api_thread.start()
            
            # Wait for connection
            time.sleep(2)
            
            if self.isConnected():
                self.connected = True
                print("[SUCCESS] Connected successfully!")
                
                # Wait for next valid order ID
                timeout = 10
                start_time = time.time()
                while self.next_order_id is None and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.next_order_id is None:
                    print("[ERROR] Failed to receive next valid order ID")
                    return False
                
                return True
            else:
                print("[ERROR] Failed to connect")
                return False
                
        except Exception as e:
            print(f"[ERROR] Connection error: {e}")
            return False
    
    def get_positions(self):
        """Request and wait for position data"""
        print("[INFO] Requesting positions...")
        self.position_event.clear()
        self.reqPositions()
        
        # Wait for position data
        if self.position_event.wait(timeout=10):
            print("[SUCCESS] Position data received")
        else:
            print("[WARNING] Timeout waiting for position data")

def main():
    """Main trading demonstration"""
    print("Clean Trading Example - Interactive Brokers API")
    print("This example demonstrates placing trades and viewing positions")
    print("IMPORTANT: Make sure IB Gateway is running on port 4001 (paper trading)")
    print("\n" + "="*80)
    
    # Create and connect the app
    app = CleanTradingApp()
    
    try:
        # Connect to IB Gateway (paper trading)
        if not app.connect_and_run(host="127.0.0.1", port=4001, client_id=1):
            print("[ERROR] Failed to connect to IB Gateway")
            return
        
        # Get current positions
        app.get_positions()
        app.display_positions()
        
        print("\n[DEMO] PLACING SAMPLE ORDERS...")
        print("(These are small test orders for demonstration)")
        
        # Example 1: Place a small market buy order
        print("\n[STEP 1] Placing market buy order for 1 share of AAPL...")
        order_id_1 = app.place_buy_order("AAPL", 1, "MKT")
        
        if order_id_1:
            # Wait a moment for order to process
            time.sleep(3)
        
        # Example 2: Place a limit buy order
        print("\n[STEP 2] Placing limit buy order for 1 share of MSFT at $250...")
        order_id_2 = app.place_buy_order("MSFT", 1, "LMT", 250.00)
        
        if order_id_2:
            # Wait a moment for order to process
            time.sleep(3)
        
        # Display orders
        app.display_orders()
        
        # Wait a bit more for any fills
        print("\n[INFO] Waiting for orders to process...")
        time.sleep(5)
        
        # Display final status
        print("\n[FINAL STATUS]")
        app.display_orders()
        
        # Get updated positions
        app.get_positions()
        app.display_positions()
        
        # Cancel any pending orders
        pending_orders = [oid for oid, order in app.orders.items() 
                         if order.status in ["PreSubmitted", "Submitted"]]
        
        if pending_orders:
            print(f"\n[CLEANUP] Cancelling {len(pending_orders)} pending orders...")
            for order_id in pending_orders:
                app.cancel_order(order_id)
                time.sleep(1)
        
        print("\n[COMPLETE] TRADING DEMONSTRATION COMPLETE")
        print("[LOG] Check 'clean_trading.log' for detailed logs")
        print("[TIP] Start with small quantities and always use paper trading first!")
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopped by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        logging.error(f"Main error: {e}")
    finally:
        # Disconnect
        if app.isConnected():
            app.disconnect()
            print("\n[DISCONNECTED] Disconnected from IB Gateway")
        
        print("\nGoodbye!")

if __name__ == "__main__":
    main()