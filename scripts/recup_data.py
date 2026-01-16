
import yfinance as yf
import pandas as pd
import os


import pandas as pd
import os
from datetime import datetime



#--- Create data directory 

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
os.makedirs(data_dir, exist_ok=True)




#--- Define assets to download ---

indices = {
    "S&P 500": "^GSPC",
    "Nasdaq Composite": "^IXIC",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
    "CAC 40": "^FCHI",
    "DAX": "^GDAXI",
    "FTSE 100": "^FTSE",
    "FTSE MIB": "FTSEMIB.MI",
    "IBEX 35": "^IBEX",
    "SMI": "^SSMI",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "Shanghai Composite": "000001.SS",
    "ASX 200": "^AXJO",
    "Bovespa": "^BVSP"
}

stocks = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "Berkshire Hathaway": "BRK-B",
    "JP Morgan": "JPM",
    "Visa": "V",
    "Mastercard": "MA",
    "Exxon Mobil": "XOM",
    "Chevron": "CVX",
    "Johnson & Johnson": "JNJ",
    "Pfizer": "PFE",
    "Coca-Cola": "KO",
    "PepsiCo": "PEP",
    "Walmart": "WMT",
    "McDonald's": "MCD",
    "Netflix": "NFLX"
}

etfs = {
    "SPDR S&P 500 ETF": "SPY",
    "Invesco QQQ": "QQQ",
    "Vanguard Total Stock Market": "VTI",
    "Vanguard FTSE All-World": "VT",
    "iShares MSCI World": "URTH",
    "iShares MSCI Emerging Markets": "EEM",
    "Vanguard FTSE Emerging Markets": "VWO",
    "iShares Core S&P 500": "IVV",
    "ARK Innovation ETF": "ARKK",
    "iShares Gold Trust": "IAU",
    "SPDR Gold Shares": "GLD",
    "Vanguard Real Estate ETF": "VNQ",
    "iShares Core Aggregate Bond": "AGG",
    "Vanguard Total Bond Market": "BND",
    "SPDR Dow Jones Industrial Average": "DIA"
}


crypto = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Binance Coin": "BNB-USD",
    "Solana": "SOL-USD",
    "Ripple": "XRP-USD",
    "Cardano": "ADA-USD",
    "Dogecoin": "DOGE-USD",
    "Avalanche": "AVAX-USD",
    "Polkadot": "DOT-USD",
    "Chainlink": "LINK-USD",
    "Polygon": "MATIC-USD",
    "Litecoin": "LTC-USD",
    "Bitcoin Cash": "BCH-USD",
    "Stellar": "XLM-USD",
    "Cosmos": "ATOM-USD"
}


commodities = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil WTI": "CL=F",
    "Brent Oil": "BZ=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F",
    "Corn": "ZC=F",
    "Wheat": "ZW=F",
    "Soybeans": "ZS=F",
    "Coffee": "KC=F",
    "Sugar": "SB=F",
    "Cotton": "CT=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",
    "Aluminum": "ALI=F"
}

assets = {
    "Index": indices,
    "Stock": stocks,
    "ETF": etfs,
    "Crypto": crypto,
    "Commodity": commodities
}






#--- Define function to clean market data ---
# This function standardizes the dataframe format for all assets
# It keeps only relevant columns, renames them, converts data types, and handles missing dates
# It have to fill forward missing dates for assets that do not trade on weekends (i.e., all except Crypto)

def clean_market_data(df, asset_type, asset_name, ticker):
    df = df.reset_index()
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_") 
    
    df = df[["date","open","close"]]

    df.insert(0, "asset_type", asset_type)
    df.insert(1, "asset_name", asset_name)
    df.insert(2, "ticker", ticker)
    # Standardize date format
    df["date"] = pd.to_datetime(df["date"])
    df["date"] = df["date"].dt.tz_localize(None)
    df["date"] = df["date"].dt.normalize() 

    price_cols = ["open","close"]
    df[price_cols] = df[price_cols].astype(float)
    df = df.sort_values("date").reset_index(drop=True)



    # Fill missing dates for non-crypto assets
    if asset_type != "Crypto":
        # It creates a complete date range from the minimum to maximum date in the data
        all_dates = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
        df = df.set_index("date").reindex(all_dates)
        df["asset_type"] = asset_type
        df["asset_name"] = asset_name
        df["ticker"] = ticker
        # Forward fill missing prices
        df[price_cols] = df[price_cols].ffill()
        df = df.reset_index().rename(columns={"index":"date"})


    return df




#--- Define function to get last date from existing data ---
def get_last_date(filepath):
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, sep=",", decimal=".", parse_dates=["date"])
        return df["date"].max()
    return None



#--- Define function to download new data ---
# This function downloads data from Yahoo Finance using yfinance
def download_new_data(ticker_symbol, start_date=None):
    ticker = yf.Ticker(ticker_symbol)
    if start_date:
        return ticker.history(start=start_date + pd.Timedelta(days=1))
    else:
        return ticker.history(period="3y")






master_file = os.path.join(data_dir, "master_data.csv")
all_data = []

#-- Check if data update is needed ---
if os.path.exists(master_file):
    df_master = pd.read_csv(master_file, sep=",", decimal=".", parse_dates=["date"])
    if not df_master.empty:
        last_date = df_master["date"].max().normalize()  # Get the last date in the master file
    else:
        last_date = None
else:
    last_date = None

today = pd.Timestamp.today().normalize()

if last_date is not None and last_date >= today - pd.Timedelta(days=1): 
    print(f"Data allready updated.")
    download_needed = False
else:
    download_needed = True



#-- Update data if needed ---
if download_needed:
    for asset_type, asset_dict in assets.items():
        for asset_name, ticker in asset_dict.items():
            print(f"\n--- Updating {asset_name} ({asset_type}) ---")
            last_date = None
            if os.path.exists(master_file):
                df_master = pd.read_csv(master_file, sep=",", decimal=".", parse_dates=["date"])
                df_master_asset = df_master[(df_master["ticker"]==ticker)]
                if not df_master_asset.empty:
                    last_date = df_master_asset["date"].max()
            print(f"[{asset_name}] Last date locally: {last_date}")

            df_raw = download_new_data(ticker, last_date)
            if df_raw.empty:
                print(f"[{asset_name}] No new data")
                continue

            df_clean = clean_market_data(df_raw, asset_type, asset_name, ticker)

            all_data.append(df_clean)
            print(f"[{asset_name}] New rows fetched: {len(df_clean)}")

if all_data:
    df_final = pd.concat(all_data)
    if os.path.exists(master_file):
        df_existing = pd.read_csv(master_file, sep=",", decimal=".", parse_dates=["date"])
        df_final = pd.concat([df_existing, df_final]).drop_duplicates(subset=["asset_type","asset_name","date"])
    df_final = df_final.sort_values(["asset_type","asset_name","date"])

    analysis_end_date = df_final["date"].max() - pd.Timedelta(days=1) # Exclude most recent date to ensure completeness for graphs in powerbi

    df_final = df_final[df_final["date"] <= analysis_end_date]


    df_final.to_csv(master_file, sep=",", decimal=".", index=False)
    
else:
    print("\nNo new data to update.")