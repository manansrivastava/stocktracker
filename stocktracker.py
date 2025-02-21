import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import requests

# 📌 Connect to SQLite Database
conn = sqlite3.connect("stocks.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS stocks (symbol TEXT, date TEXT, price REAL)")
conn.commit()

def fetch_nse_stock_list():
    """Fetch all Indian stock symbols & company names from NSE India."""
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"  # Nifty 500 stocks
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com",
        "Connection": "keep-alive"
    }
    
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)  # Establish session
    
    try:
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
        
        data = response.json()
        
        stock_list = []
        for stock in data.get("data", []):
            stock_list.append({"Company Name": stock["symbol"], "Stock Symbol": stock["symbol"] + ".NS"})
        
        df = pd.DataFrame(stock_list)
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching stock list: {e}")
        return None

def get_stock_details(ticker):
    """Fetch and display stock details."""
    stock = yf.Ticker(ticker + ".NS")
    info = stock.info

    details = {
        "Current Price": info.get("currentPrice"),
        "52W High": info.get("fiftyTwoWeekHigh"),
        "52W Low": info.get("fiftyTwoWeekLow"),
        "Market Cap": info.get("marketCap"),
        "P/E Ratio": info.get("trailingPE"),
        "Dividend Yield": info.get("dividendYield"),
        "Previous Close": info.get("previousClose")
    }

    return details

def get_stock_price(ticker):
    """Fetch historical stock data."""
    stock = yf.Ticker(ticker + ".NS")
    data = stock.history(period="6mo")
    return data

def save_to_db(ticker, price):
    """Save stock prices to the database."""
    cursor.execute("INSERT INTO stocks (symbol, date, price) VALUES (?, DATE('now'), ?)", (ticker, price))
    conn.commit()

def track_multiple_stocks(tickers):
    """Fetch and plot multiple stocks' prices."""
    plt.figure(figsize=(10, 5))
    
    for ticker in tickers:
        data = get_stock_price(ticker)
        if not data.empty:
            plt.plot(data.index, data["Close"], label=ticker)
            save_to_db(ticker, data["Close"].iloc[-1])  # Save latest price
    
    plt.xlabel("Date")
    plt.ylabel("Stock Price (₹)")
    plt.title("Stock Price Comparison")
    plt.legend()
    plt.grid()
    plt.show()

def plot_with_moving_averages(ticker):
    """Plot stock price with 50-day & 200-day Moving Averages."""
    data = get_stock_price(ticker)
    
    if data.empty:
        print(f"⚠️ No data available for {ticker}")
        return
    
    data["50_MA"] = data["Close"].rolling(50).mean()
    data["200_MA"] = data["Close"].rolling(200).mean()
    
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data["Close"], label="Closing Price", color="blue")
    plt.plot(data.index, data["50_MA"], label="50-day MA", color="orange")
    plt.plot(data.index, data["200_MA"], label="200-day MA", color="red")
    
    plt.xlabel("Date")
    plt.ylabel("Stock Price (₹)")
    plt.title(f"{ticker} Stock Trend with Moving Averages")
    plt.legend()
    plt.grid()
    plt.show()

# 🚀 User Choice Menu
while True:
    print("\n🔹 Stock Market Tracker (NSE India) 🔹")
    print("1️⃣ View NSE Stock List")
    print("2️⃣ Get Real-time Stock Price")
    print("3️⃣ Fetch Stock Details")
    print("4️⃣ Track Multiple Stocks")
    print("5️⃣ Plot Moving Averages for a Stock")
    print("6️⃣ Exit")
    choice = input("Select an option (1-6): ")

    if choice == "1":
        df = fetch_nse_stock_list()
        if df is not None:
            print("\n🔹 NSE India Stock List:")
            print(df.to_string(index=False))

    elif choice == "2":
        stock_symbol = input("Enter stock ticker (e.g., TCS, RELIANCE, INFY): ").upper()
        data = get_stock_price(stock_symbol)
        if not data.empty:
            latest_price = data["Close"].iloc[-1]
            print(f"\n✅ {stock_symbol} Current Price: ₹{latest_price}")
        else:
            print("⚠️ No data available!")

    elif choice == "3":
        stock_symbol = input("Enter stock ticker (e.g., TCS, RELIANCE, INFY): ").upper()
        details = get_stock_details(stock_symbol)
        print("\n🔹 Stock Details:")
        for key, value in details.items():
            print(f"{key}: {value}")

    elif choice == "4":
        stock_symbols = input("Enter stock tickers (comma-separated, e.g., TCS, RELIANCE, INFY): ").upper().split(", ")
        track_multiple_stocks(stock_symbols)

    elif choice == "5":
        stock_symbol = input("Enter stock ticker (e.g., TCS, RELIANCE, INFY): ").upper()
        plot_with_moving_averages(stock_symbol)

    elif choice == "6":
        print("✅ Exiting...")
        break

    else:
        print("⚠️ Invalid choice! Please enter a number between 1-6.")

# Close DB connection
conn.close()
