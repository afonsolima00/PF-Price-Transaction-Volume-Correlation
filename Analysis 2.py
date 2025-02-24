# Created with ChatGPT and search on perplexity

import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
import time
import json

# API Configuration
ETHERSCAN_API_KEY = "M8NZU3KCC4U5H6NFS19DTFFU2FUVCHB8ZB"
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart"

def fetch_total_supply(days=30):
    """Fetch Ethereum's total supply over a period of days."""
    url = "https://api.etherscan.io/api"
    data = []
    
    print("Starting to fetch total supply data...")
    
    for day in range(days):
        date = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
        
        params = {
            "module": "stats",
            "action": "ethsupply",  # Changed from ethsupply2 to ethsupply
            "apikey": ETHERSCAN_API_KEY
        }
        
        try:
            print(f"Fetching data for {date}...")
            response = requests.get(url, params=params)
            result = response.json()
            
            print(f"API Response: {json.dumps(result, indent=2)}")
            
            if result["status"] == "1" and "result" in result:
                # For ethsupply endpoint, result is directly the supply value
                total_supply = int(result["result"]) / 10**18
                data.append({"date": date, "total_supply": total_supply})
                print(f"Successfully processed data for {date}")
            else:
                error_msg = result.get("result", "Unknown error")
                print(f"Etherscan API Error: {error_msg}")
                break
            
            # Respect rate limits (5 calls per second)
            time.sleep(0.21)
        
        except Exception as e:
            print(f"An error occurred while fetching total supply: {str(e)}")
            print(f"Full error details: {type(e).__name__}")
            break
    
    if not data:
        print("No data was collected!")
        return pd.DataFrame()
    
    print(f"Collected {len(data)} days of supply data")
    return pd.DataFrame(data)

def fetch_price_data(days=30):
    """Fetch historical price data from CoinGecko."""
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    
    print("Starting to fetch price data...")
    
    try:
        response = requests.get(COINGECKO_URL, params=params)
        print(f"CoinGecko Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"CoinGecko Error Response: {response.text}")
            return pd.DataFrame()
            
        data = response.json()
        
        if "prices" not in data:
            print(f"Unexpected response structure: {json.dumps(data, indent=2)}")
            return pd.DataFrame()

        df = pd.DataFrame([
            {
                "date": datetime.fromtimestamp(price[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
                "price": price[1]
            } for price in data["prices"]
        ])
        
        print(f"Successfully collected {len(df)} price data points")
        return df
    
    except Exception as e:
        print(f"An error occurred while fetching price data: {str(e)}")
        print(f"Full error details: {type(e).__name__}")
        return pd.DataFrame()

def analyze_correlation():
    """Main analysis function."""
    print("\n=== Starting Analysis ===\n")
    
    print("Fetching total supply...")
    supply_data = fetch_total_supply(30)
    
    if supply_data.empty:
        print("Failed to fetch supply data")
        return
    
    print("\nSupply data summary:")
    print(supply_data.head())
    print(f"Supply data shape: {supply_data.shape}")
    
    print("\nFetching price data...")
    price_data = fetch_price_data(30)
    
    if price_data.empty:
        print("Failed to fetch price data")
        return
    
    print("\nPrice data summary:")
    print(price_data.head())
    print(f"Price data shape: {price_data.shape}")
    
    # Merge datasets on date
    supply_data["date"] = pd.to_datetime(supply_data["date"])
    price_data["date"] = pd.to_datetime(price_data["date"])
    
    print("\nMerging datasets...")
    merged = pd.merge(supply_data, price_data, on="date")
    print(f"Merged data shape: {merged.shape}")
    
    merged["price_change"] = merged["price"].pct_change() * 100
    
    # Drop any rows with NaN values
    merged = merged.dropna()
    
    if merged.empty:
        print("No overlapping data points found after merging")
        return
    
    print("\nFinal merged data summary:")
    print(merged.head())
    print(f"Final data shape: {merged.shape}")
    
    # Calculate correlation
    correlation = merged["total_supply"].corr(merged["price_change"])
    
    # Plot results
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Total Supply (Ether)', color='tab:blue')
    ax1.plot(merged["date"], merged["total_supply"], color='tab:blue', label="Total Supply")
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Price Change (%)', color='tab:red')
    ax2.plot(merged["date"], merged["price_change"], color='tab:red', label="Price Change (%)")
    ax2.tick_params(axis='y', labelcolor='tab:red')
    
    plt.title(f"Total Supply vs Price Changes (Correlation: {correlation:.2f})")
    plt.xticks(rotation=45)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    plt.savefig('correlation_analysis.png')
    print("\nPlot saved as 'correlation_analysis.png'")
    plt.close()
    
    return correlation

# Execute analysis
if __name__ == "__main__":
    correlation_score = analyze_correlation()
    
    if correlation_score is not None:
        print(f"\nFinal Results:")
        print(f"Pearson Correlation Coefficient: {correlation_score:.2f}")
