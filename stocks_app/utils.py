import yfinance as yf
import pandas as pd
from datetime import datetime
from stocks_app.models import StockData  # Import your model

def add_initial_data():
    stocks = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK.B", "UNH", "JNJ",
    "XOM", "JPM", "V", "PG", "AVGO", "HD", "MA", "LLY", "CVX", "ABBV",
    "MRK", "PEP", "KO", "COST", "WMT", "MCD", "NFLX", "ADBE", "AMD", "INTC"
]
    period = "5d"
    interval = "1m"
    
    now = int(datetime.now().timestamp())  # Converts datetime object to Unix time (seconds)

    for ticker in stocks:
        print(f"Fetching data for {ticker}...")
        try:
            data = yf.download(ticker, period=period, interval=interval)
            if data.empty:
                print(f"No data found for {ticker}")
                continue

            data.reset_index(inplace=True)  # Ensure Datetime is a column
            
            # Convert datetime column safely
            data["Datetime"] = pd.to_datetime(data["Datetime"])  # Ensure it's a datetime object
            data["Datetime"] = data["Datetime"].astype("int64") // 10**9  # Convert to UNIX timestamp

            # Calculate shift
            first_timestamp = data["Datetime"].iloc[0]
            time_shift = now - first_timestamp

            # Apply shift
            data["Datetime"] += time_shift
            
            # Save to database
            for _, row in data.iterrows():
                stock_data = StockData(
        ticker=ticker,
    datetime=row['Datetime'].item(),  # Extract scalar value
    open_price=row['Open'],
    high_price=row['High'],
    low_price=row['Low'],
    close_price=row['Close'],
    volume=row['Volume']
)
                stock_data.save()
            print(f"Saved shifted {ticker} data to SQLite")
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    print("Data fetching complete!")


def initialise_db():
    print("Flushing SQLite database...")
    StockData.objects.all().delete()
    print("Repopulating database with initial data...")
    add_initial_data()
    print("Database initialization complete.")
