import yfinance as yf
import pandas as pd
from datetime import datetime
from stocks_app.models import StockData  # Import your model

def add_initial_data():

    nse_stocks = [
        "AAPL", "MSFT"
    ]

    # Define parameters
    period = "5d"
    interval = "1m"
    now = datetime.now()  # Keep as tz-naive for consistency

    # Fetch data for each stock
    for ticker in nse_stocks:
        print(f"Fetching data for {ticker}...")
        try:
            data = yf.download(ticker, period=period, interval=interval)
            if not data.empty:
                # Reset index to move timestamps into a column
                data.reset_index(inplace=True)
                
                # Convert 'Datetime' column to tz-naive
                data["Datetime"] = data["Datetime"].dt.tz_convert(None)
                
                # Calculate the time difference from the first timestamp to "now"
                time_shift = now - data["Datetime"].iloc[0]
                
                # Shift all timestamps
                data["Datetime"] = data["Datetime"] + time_shift
                print(data["Datetime"])
                # add to StockData
                for _, row in data.iterrows():
                    stock_data = StockData(
                        ticker=ticker,
                        datetime=row['Datetime'],
                        open_price=row['Open'],
                        high_price=row['High'],
                        low_price=row['Low'],
                        close_price=row['Close'],
                        volume=row['Volume']
                    )
                    stock_data.save()
                print(f"Saved shifted {ticker} data to SQLite")            
                
                


                print(f"Saved shifted {ticker} data to SQLlite")
            else:
                print(f"No data found for {ticker}")
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    print("Data fetching complete!")
def initialise_db():
    print("Flushing SQLite database...")
    
    # Flush the database (removes all data but keeps migrations)
    StockData.objects.all().delete()


    print("Repopulating database with initial data...")
    add_initial_data()  # Call function to add data

    print("Database initialization complete.")
