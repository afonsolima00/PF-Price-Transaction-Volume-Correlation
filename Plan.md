# 1st Step

Objective: Prepare the Python environment with necessary libraries.
Action:
Install required libraries: requests for API calls, pandas for data manipulation, and matplotlib for visualization.
Use a Jupyter Notebook to document the process and findings.

# 2nd Step

Objective: Specify the blockchain, metric, and date range for data collection.
Action:
Blockchain: Choose Ethereum Layer 1 (due to its well-established APIs like Etherscan).
Metric: Use transaction volume, interpreted as the daily number of transactions (consistent with the task’s context).
Date Range: Set a fixed range from January 1, 2017, to December 31, 2022, to capture multiple market cycles while keeping the dataset manageable.

# 3rd Step

Objective: Retrieve data the Etherscan API.
Action:
Use the Etherscan API endpoint module=stats&action=dailytx to fetch daily transaction counts.
Parse the response into a pandas DataFrame with dates and transaction counts.

# 4th Step

Objective: Obtain daily price data for Ethereum using the CoinGecko API.
Action:
Use the CoinGecko /market_chart/range endpoint to fetch historical daily prices in USD.
Convert timestamps to dates and average prices per day if necessary.

# 5th Step

Objective: Combine transaction and price data and compute price returns.
Action:
Merge the DataFrames on the date column.
Calculate daily returns as the percentage change in price.
Handle missing data by dropping rows with NaN values.

# 6th Step

Step 6: Analyze Correlations
Objective: Compare transaction volume with short-term market movements (same-day and next-day returns).
Action:
Compute the Pearson correlation between transaction counts and same-day returns.
Compute the correlation between transaction counts and next-day returns (shifted returns).

# 7th Step

Objective: Create plots to explore trends and relationships visually.
Action:
Plot time series of transaction counts and prices.
Create scatter plots of transaction counts vs. same-day and next-day returns.

# 8th Step 

Objective: Document insights in a concise report within the Jupyter Notebook.
Action:
Add markdown cells to explain the methodology and results.
Discuss correlation values and visual observations.
Suggest implications for trading strategies.