# 📈 Interactive Brokers Trading Guide

## 🚀 How to Place Trades and Monitor Positions

This guide shows you how to place buy/sell orders and monitor your positions using the Interactive Brokers API.

## ⚠️ **IMPORTANT SAFETY NOTICE**

### **🔴 Paper Trading vs Live Trading**

| Mode | Port | Risk | Purpose |
|------|------|------|----------|
| **Paper Trading** | 4001 | ✅ **SAFE** | Testing with virtual money |
| **Live Trading** | 4000 | ⚠️ **REAL MONEY** | Actual trading with real funds |

**🛡️ ALWAYS START WITH PAPER TRADING (Port 4001) TO TEST YOUR CODE!**

## 📋 **Prerequisites**

1. **IB Gateway or TWS running**
2. **API enabled** in settings
3. **Paper trading account** (recommended for testing)
4. **Enhanced code** from previous improvements

## 🎯 **Quick Start - Place Your First Trade**

### **Step 1: Run the Trading Example**

```bash
# Make sure you're in the project directory
cd c:\Users\amari\Desktop\MartinGales

# Activate virtual environment
.\env\Scripts\activate

# Run the trading example
python trading_example.py
```

### **Step 2: What You'll See**

```
=== CURRENT POSITIONS ===
Symbol     Quantity   Avg Cost     Market Value    P&L
------------------------------------------------------
AAPL       100        $150.00      $15,200.00      $200.00
MSFT       50         $300.00      $15,100.00      $100.00

=== PLACING SAMPLE ORDERS ===
Placed MKT BUY order for 10 shares of AAPL (Order ID: 1)
Placed LMT BUY order for 5 shares of MSFT (Order ID: 2)
Limit Price: $300.00

=== ORDER STATUS ===
Order ID   Status       Filled   Remaining  Avg Price
-----------------------------------------------------
1          Filled       10       0          $152.50
2          Submitted    0        5          N/A
```

## 🛠️ **How to Place Different Types of Orders**

### **1. Market Buy Order (Immediate Execution)**

```python
# Buy 10 shares of Apple at current market price
order_id = app.place_buy_order("AAPL", 10, "MKT")
```

### **2. Limit Buy Order (Specific Price)**

```python
# Buy 5 shares of Microsoft only if price is $300 or lower
order_id = app.place_buy_order("MSFT", 5, "LMT", 300.00)
```

### **3. Market Sell Order**

```python
# Sell 10 shares of Apple at current market price
order_id = app.place_sell_order("AAPL", 10, "MKT")
```

### **4. Limit Sell Order**

```python
# Sell 5 shares of Microsoft only if price is $350 or higher
order_id = app.place_sell_order("MSFT", 5, "LMT", 350.00)
```

### **5. Cancel an Order**

```python
# Cancel order by ID
app.cancel_order(order_id)
```

## 📊 **Where to See Your Positions**

### **1. In the Console Output**
```
=== CURRENT POSITIONS ===
Symbol     Quantity   Avg Cost     Market Value    P&L
------------------------------------------------------
AAPL       110        $151.25      $16,720.00      $225.00
MSFT       55         $299.50      $16,500.00      $275.00
```

### **2. In the Log File**
```bash
# Check detailed logs
type trading_api.log
```

### **3. In IB Gateway/TWS**
- **Portfolio tab** - Shows all positions
- **Account tab** - Shows account value and P&L
- **Orders tab** - Shows order status

### **4. Programmatically**
```python
# Access positions in your code
for symbol, position in app.positions.items():
    print(f"{position.symbol}: {position.position} shares @ ${position.average_cost:.2f}")
```

## 🔍 **Understanding Order Status**

| Status | Meaning |
|--------|----------|
| **PreSubmitted** | Order received, being validated |
| **Submitted** | Order sent to exchange |
| **Filled** | ✅ Order completely executed |
| **PartiallyFilled** | 🟡 Order partially executed |
| **Cancelled** | ❌ Order cancelled |
| **Rejected** | ❌ Order rejected by exchange |

## 💡 **Complete Trading Example**

```python
def trading_strategy_example():
    """Example trading strategy"""
    app = TradingApp()
    
    # Connect and wait
    app.connect("127.0.0.1", 4001, 1)
    # ... connection code ...
    
    # 1. Check current positions
    app.display_positions()
    
    # 2. Place a conservative buy order
    if "AAPL_STK" not in app.positions:
        # Buy 10 shares of Apple with limit order
        order_id = app.place_buy_order("AAPL", 10, "LMT", 200.00)
        print(f"Placed buy order: {order_id}")
    
    # 3. Wait for order to fill
    time.sleep(10)
    
    # 4. Check if order filled
    if order_id in app.orders:
        status = app.orders[order_id].status
        if status == "Filled":
            print("✅ Order filled successfully!")
            app.display_positions()
        elif status in ["PreSubmitted", "Submitted"]:
            print("⏳ Order still pending...")
            # Optionally cancel if taking too long
            app.cancel_order(order_id)
    
    # 5. Set a profit target (sell order)
    if "AAPL_STK" in app.positions:
        current_qty = app.positions["AAPL_STK"].position
        if current_qty > 0:
            # Sell at 5% profit
            avg_cost = app.positions["AAPL_STK"].average_cost
            target_price = avg_cost * 1.05
            
            sell_order_id = app.place_sell_order("AAPL", int(current_qty), "LMT", target_price)
            print(f"Set profit target at ${target_price:.2f}")
```

## 🛡️ **Risk Management Best Practices**

### **1. Start Small**
```python
# Start with small quantities
order_id = app.place_buy_order("AAPL", 1, "MKT")  # Just 1 share
```

### **2. Use Limit Orders**
```python
# Control your entry price
order_id = app.place_buy_order("AAPL", 10, "LMT", 200.00)  # Won't pay more than $200
```

### **3. Set Stop Losses**
```python
# Example: Sell if price drops 5% below purchase price
stop_price = purchase_price * 0.95
stop_order_id = app.place_sell_order("AAPL", quantity, "LMT", stop_price)
```

### **4. Monitor Positions Regularly**
```python
# Check positions every few minutes
while True:
    app.display_positions()
    time.sleep(300)  # Check every 5 minutes
```

## 📱 **Real-Time Position Monitoring**

### **Method 1: Console Display**
```python
# Continuous monitoring
def monitor_positions(app):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
        print(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        app.display_positions()
        app.display_orders()
        time.sleep(30)  # Update every 30 seconds
```

### **Method 2: Log File Monitoring**
```bash
# Windows - Monitor log file in real-time
Get-Content trading_api.log -Wait -Tail 10

# Or use PowerShell
tail -f trading_api.log
```

### **Method 3: IB Gateway/TWS Interface**
- Open **Portfolio** tab for real-time positions
- Open **Account** tab for P&L updates
- Open **Orders** tab for order status

## 🚨 **Common Issues & Solutions**

### **Issue: "Order Rejected"**
**Solutions:**
- Check if you have sufficient buying power
- Verify the stock symbol is correct
- Ensure market is open (9:30 AM - 4:00 PM ET)
- Check if you have market data permissions

### **Issue: "No Positions Showing"**
**Solutions:**
```python
# Force position refresh
app.reqPositions()
time.sleep(2)
app.display_positions()
```

### **Issue: "Connection Lost"**
**Solutions:**
- Restart IB Gateway/TWS
- Check API settings are enabled
- Verify port number (4001 for paper, 4000 for live)

## 📊 **Advanced Position Tracking**

### **Export Positions to CSV**
```python
import csv
from datetime import datetime

def export_positions_to_csv(app):
    filename = f"positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Symbol', 'Quantity', 'Avg Cost', 'Market Price', 'Market Value', 'P&L'])
        
        for key, pos in app.positions.items():
            market_value = pos.market_price * pos.position
            pnl = (pos.market_price - pos.average_cost) * pos.position
            
            writer.writerow([
                pos.symbol,
                pos.position,
                pos.average_cost,
                pos.market_price,
                market_value,
                pnl
            ])
    
    print(f"Positions exported to {filename}")
```

### **Calculate Portfolio Metrics**
```python
def calculate_portfolio_metrics(app):
    total_value = 0
    total_pnl = 0
    
    for key, pos in app.positions.items():
        market_value = pos.market_price * pos.position
        pnl = (pos.market_price - pos.average_cost) * pos.position
        
        total_value += market_value
        total_pnl += pnl
    
    print(f"\n=== PORTFOLIO SUMMARY ===")
    print(f"Total Market Value: ${total_value:,.2f}")
    print(f"Total P&L: ${total_pnl:,.2f}")
    print(f"Total Return: {(total_pnl/total_value)*100:.2f}%" if total_value > 0 else "N/A")
```

## 🎯 **Next Steps**

1. **Test with Paper Trading**: Always test your strategies with virtual money first
2. **Start Small**: Begin with small position sizes
3. **Monitor Closely**: Watch your positions and orders carefully
4. **Learn Gradually**: Add more complex order types as you gain experience
5. **Risk Management**: Always have exit strategies and stop losses

## 📞 **Getting Help**

- **IB API Documentation**: [Interactive Brokers API Guide](https://interactivebrokers.github.io/tws-api/)
- **Log Files**: Check `trading_api.log` for detailed information
- **IB Support**: Contact Interactive Brokers support for account issues

---

**Remember: Trading involves risk. Always start with paper trading and never risk more than you can afford to lose!** 🛡️