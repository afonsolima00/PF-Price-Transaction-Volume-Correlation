# Written by Claude Sonnet in Copilot

import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Global variable to track last request time for rate limiting
_last_request_time = 0


def limited_get(url: str, headers: dict = None) -> requests.Response:
    """
    Performs a GET request ensuring that no more than 5 requests per second are made.
    This function enforces a minimum delay of 0.2 seconds between requests.

    Args:
        url (str): The URL to request.
        headers (dict, optional): HTTP headers to include in the request.

    Returns:
        requests.Response: The HTTP response.
    """
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    delay = 0.2
    if elapsed < delay:
        time.sleep(delay - elapsed)
    response = requests.get(url, headers=headers)
    _last_request_time = time.time()
    return response

# Parameters
ETHERSCAN_API_KEY = 'INSERT_YOUR_API_KEY'  # Replace with your valid API key
START_DATE = '2022-12-01'
END_DATE = '2022-12-31'


def verify_api_key(api_key: str) -> bool:
    """
    Verifies the provided Etherscan API key by retrieving the Ethereum supply.

    Args:
        api_key (str): The Etherscan API key.

    Returns:
        bool: True if the API key is valid.

    Raises:
        ValueError: If the API key is invalid.
    """
    test_url = f"https://api.etherscan.io/api?module=stats&action=ethsupply&apikey={api_key}"
    response = limited_get(test_url)
    data = response.json()
    if data.get('status') != '1':
        raise ValueError(f"Invalid API key. Error: {data.get('message')}")
    return True


def fetch_transaction_data(api_key: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches daily Ethereum transaction count data from Etherscan for the specified date range.

    Args:
        api_key (str): The Etherscan API key.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: DataFrame containing 'date' and 'transaction_count'.
    """
    print("Verifying Etherscan API key...")
    verify_api_key(api_key)
    
    print("Fetching transaction data from Etherscan...")
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())

    url = (f"https://api.etherscan.io/api?module=stats&action=dailytx&"
           f"startdate={start_ts}&enddate={end_ts}&sort=asc&apikey={api_key}")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = limited_get(url)
            data = response.json()
            if data.get('status') == '1' and 'result' in data:
                df = pd.DataFrame(data['result'])
                df['date'] = pd.to_datetime(df['UTCDate'])
                df['transaction_count'] = df['value'].astype(int)
                return df[['date', 'transaction_count']]
            else:
                if attempt == max_retries - 1:
                    raise Exception(f"Error fetching transaction data: {data.get('message', 'Unknown error')}")
                print(f"Transaction data fetch attempt {attempt + 1} failed. Retrying...")
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Network error: {str(e)}")
            print(f"Network error on attempt {attempt + 1}: {str(e)}. Retrying...")
            time.sleep(5)
    return pd.DataFrame()


def fetch_price_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches Ethereum price data from CoinGecko for the specified date range.

    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: DataFrame containing 'date' and average 'price'.
    """
    print("Fetching price data from CoinGecko...")
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())

    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    url = (f"https://api.coingecko.com/api/v3/coins/ethereum/market_chart/range?"
           f"vs_currency=usd&from={start_ts}&to={end_ts}")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = limited_get(url, headers=headers)
            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 60))
                print(f"Rate limit reached. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            data = response.json()
            if 'prices' not in data:
                raise Exception(f"Unexpected response format: {data}")
            prices = data['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.date
            df['date'] = pd.to_datetime(df['date'])
            return df.groupby('date')['price'].mean().reset_index()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to fetch price data after {max_retries} attempts: {str(e)}")
            print(f"Price data fetch attempt {attempt + 1} failed: {str(e)}. Retrying...")
            time.sleep(5)
    return pd.DataFrame()


def run_analysis():
    """
    Runs the analysis by fetching transaction and price data, merging them, performing correlation analysis,
    and generating visualizations. Saves results to CSV and PNG files.
    """
    print("Starting analysis...")
    print(f"Date range: {START_DATE} to {END_DATE}\n")

    try:
        tx_df = fetch_transaction_data(ETHERSCAN_API_KEY, START_DATE, END_DATE)
        print("Transaction data sample:")
        print(tx_df.head(), "\n")
    except Exception as e:
        print(f"Error fetching transaction data: {e}")
        return

    time.sleep(2)  # Respect rate limits between API calls
    try:
        price_df = fetch_price_data(START_DATE, END_DATE)
        print("Price data sample:")
        print(price_df.head(), "\n")
    except Exception as e:
        print(f"Error fetching price data: {e}")
        return

    if tx_df.empty or price_df.empty:
        print("Insufficient data for analysis.")
        return

    merged_df = pd.merge(tx_df, price_df, on='date', how='inner')
    if merged_df.empty:
        print("No overlapping data found between transaction and price datasets.")
        return

    merged_df['return'] = merged_df['price'].pct_change()
    merged_df = merged_df.dropna()
    if merged_df.empty:
        print("Merged data empty after processing.")
        return

    same_day_corr = merged_df['transaction_count'].corr(merged_df['return'])
    next_day_return = merged_df['return'].shift(-1)
    next_day_corr = merged_df['transaction_count'].corr(next_day_return)

    print(f"Same-day correlation: {same_day_corr:.4f}")
    print(f"Next-day correlation: {next_day_corr:.4f}\n")

    merged_df.to_csv('ethereum_analysis_results.csv', index=False)
    print("Analysis results saved to ethereum_analysis_results.csv")

    # Generate visualizations
    plt.style.use('seaborn')
    
    # Time series plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    ax1.plot(merged_df['date'], merged_df['transaction_count'], 'b-')
    ax1.set_title('Daily Transaction Count')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Transaction Count')

    ax2.plot(merged_df['date'], merged_df['price'], 'g-')
    ax2.set_title('Ethereum Price (USD)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Price (USD)')

    plt.tight_layout()
    plt.savefig('time_series_analysis.png')
    plt.close()

    # Correlation scatter plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.scatter(merged_df['transaction_count'], merged_df['return'])
    ax1.set_title(f'Same-Day Correlation: {same_day_corr:.4f}')
    ax1.set_xlabel('Transaction Count')
    ax1.set_ylabel('Daily Return')

    ax2.scatter(merged_df['transaction_count'], next_day_return)
    ax2.set_title(f'Next-Day Correlation: {next_day_corr:.4f}')
    ax2.set_xlabel('Transaction Count')
    ax2.set_ylabel('Next-Day Return')

    plt.tight_layout()
    plt.savefig('correlation_analysis.png')
    plt.close()

    print("Visualization plots saved as:")
    print("- time_series_analysis.png")
    print("- correlation_analysis.png")


if __name__ == "__main__":
    run_analysis()
