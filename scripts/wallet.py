import pandas as pd
import os
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
master_file = os.path.join(data_dir, "master_data.csv")
portfolio_file = os.path.join(data_dir, "user_portfolio.csv")



# --- Load existing portfolio ---
if os.path.exists(portfolio_file):
    df_portfolio = pd.read_csv(portfolio_file, sep=",", parse_dates=["purchase_date"])
    print("Current portfolio:")
    if df_portfolio.empty:
        print("No assets present.")
    else:
        print(df_portfolio.to_string(index=False))
else:
    df_portfolio = pd.DataFrame(columns=["ticker","quantity","purchase_date"])
    print("No existing portfolio. You will create your own.\n")

# --- Interactive management ---
while True:
    print("\nWhat do you want to do?")
    print("1 - Add an asset")
    print("2 - Remove an asset")
    print("3 - Finish and save")
    choice = input("Choice (1/2/3): ")
    if choice == "1":
        ticker = input("Enter the ticker (ex: AAPL, BTC-USD): ").upper()
        
        # Quantity input with validation
        while True:
            try:
                qty = float(input("Quantity held: "))
                if qty <= 0:
                    raise ValueError
                break
            except ValueError:
                print("Please enter a valid number.")
        
        # Purchase date input with validation
        while True:
            date_input = input("Purchase date (YYYY-MM-DD): ")
            try:
                purchase_date = pd.to_datetime(date_input)
                if purchase_date > pd.Timestamp.today().normalize():
                    print("Purchase date cannot be in the future")
                    continue
                break
            except ValueError:
                print("Incorrect format. Correct example: 2025-01-05")
        

        # Check if the asset already exists with the same purchase date
        mask = ((df_portfolio["ticker"] == ticker) & 
        (df_portfolio["purchase_date"] == pd.to_datetime(purchase_date)))
        # Update quantity if exists, else add new entry
        if mask.any():
            df_portfolio.loc[mask, "quantity"] += qty
            print(f" {ticker} updated.")
        else:
            df_portfolio = pd.concat([df_portfolio,pd.DataFrame([{"ticker":ticker,"quantity":qty,"purchase_date":purchase_date}])], ignore_index=True)
            print(f"{ticker} added to the portfolio.")


    elif choice == "2":
        # Remove an asset
        if df_portfolio.empty:
            print("The portfolio is empty, nothing to remove.")
            continue
        print("\nCurrent portfolio:")
        print(df_portfolio.to_string(index=False))
        ticker_remove = input("Enter the ticker to remove: ").upper()
        if ticker_remove in df_portfolio["ticker"].values:
            df_portfolio = df_portfolio[df_portfolio["ticker"] != ticker_remove]
            print(f"{ticker_remove} removed from the portfolio.")
        else:
            print(f"{ticker_remove} not found in the portfolio.")

    elif choice == "3":
        # Finish
        break
    else:
        print("Invalid choice, please try again.")

# --- Save the portfolio ---
df_portfolio.to_csv(portfolio_file, sep=",", index=False)
print(f"\nPortfolio saved to {portfolio_file}")
# --- Calculations with master CSV ---
if not os.path.exists(master_file):
    print(f"\nERROR: The master_data.csv file does not exist in {data_dir}")
    input("\nPress any key to close...")
    exit()

df_master = pd.read_csv(master_file, sep=",", decimal=".", parse_dates=["date"])
results = []
price_at_purchase_list = []
value_purchase_list = []
asset_name_list = []
asset_type_list = []

portfolio_tickers = df_portfolio["ticker"].unique()

df_common = df_master[df_master["ticker"].isin(portfolio_tickers)]

# Find the latest date where all portfolio tickers have data
date_counts = df_common.groupby("date")["ticker"].nunique()
last_common_date = date_counts[date_counts == len(portfolio_tickers)].index.max()

print(f"\n📌 Portfolio valued at common date: {last_common_date.date()}")

for _, asset in df_portfolio.iterrows():
    ticker = asset["ticker"]
    qty = asset["quantity"]
    purchase_date = pd.to_datetime(asset["purchase_date"])
    purchase_date = purchase_date.tz_localize(None)
    purchase_date = purchase_date.normalize()
    
    df_asset = df_master[df_master["ticker"] == ticker].sort_values("date")
    if df_asset.empty:
        print(f"\nWARNING: Ticker {ticker} not found in the master CSV.")
        continue

    df_after_purchase = df_asset[df_asset["date"] >= purchase_date]
    if df_after_purchase.empty:
        print(f"\nWARNING: No data for {ticker} after {purchase_date.date()}")
        continue

    price_at_purchase = df_after_purchase.iloc[0]["close"]


    df_at_common_date = df_asset[df_asset["date"] <= last_common_date]
    if df_at_common_date.empty:
        print(f"\nWARNING: No valid price for {ticker} at the common date.")
        continue
    latest_price = df_at_common_date.iloc[-1]["close"]


    asset_name = df_asset.iloc[0]["asset_name"]
    asset_type = df_asset.iloc[0]["asset_type"]
    value_current = qty * latest_price
    value_purchase = qty * price_at_purchase
    pct_return = (value_current - value_purchase) / value_purchase * 100
    
    price_at_purchase_list.append(price_at_purchase)
    value_purchase_list.append(value_purchase)
    asset_name_list.append(asset_name)
    asset_type_list.append(asset_type)

    results.append({
        "ticker": ticker,
        "quantity": qty,
        "purchase_date": purchase_date.date(),
        "price_at_purchase": price_at_purchase,
        "latest_price": latest_price,
        "value_current": value_current,
        "pct_return": pct_return
    })
df_portfolio["asset_name"] = asset_name_list
df_portfolio["asset_type"] = asset_type_list
df_portfolio["price_at_purchase"] = price_at_purchase_list
df_portfolio["value_purchase"] = value_purchase_list
df_portfolio["valuation_date"] = last_common_date.date()

# --- Save the portfolio ---
df_portfolio.to_csv(portfolio_file, sep=",", index=False)
print(f"\nPortfolio saved to {portfolio_file}")



# --- Final display ---
df_results = pd.DataFrame(results)
if not df_results.empty:
    print("\n--- Your updated portfolio ---")
    print(df_results.to_string(index=False))
else:
    print("\nNo valid assets found to calculate the portfolio.")

input("\nPress any key to close...")
