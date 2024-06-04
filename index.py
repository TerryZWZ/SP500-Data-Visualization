# Import necessary libraries
import yfinance as yf  # Yahoo Finance to fetch financial data
import pandas as pd  # Pandas for data manipulation
import pandas_datareader as pdr  # Data reader to fetch financial data
import argparse  # Module for parsing command-line arguments
import requests  # HTTP library for making requests
import numpy as np  # NumPy for numerical computations
import matplotlib.pyplot as plt  # Matplotlib for plotting
import matplotlib.cm as cm  # Matplotlib's colormap module
import matplotlib.font_manager as fm  # Font manager for custom fonts
import matplotlib.patheffects as path_effects  # For text effects in plots
from bs4 import BeautifulSoup  # BeautifulSoup for web scraping
from datetime import datetime  # Datetime for handling dat

# Define a function to parse command-line arguments
def get_argument():
    parser = argparse.ArgumentParser(description="Process an integer")
    parser.add_argument("-n", "--number", type=int, default=5, help="An integer value")
    args = parser.parse_args()

    # Limit the input to a maximum of 500 or minimum of 0
    if args.number > 500 or args.number < 0:
        args.number = 500

    print(f"{args.number} tickers")

    return args.number

# Function to convert market capitalization text to a numerical value
def convert_text(market_cap_text):
    market_cap = market_cap_text.replace(',', '').replace('$', '')
    multipliers = {
        'trillion': 1e12,
        'billion': 1e9,
        'million': 1e6,
        'thousand': 1e3
    }

    for key in multipliers:
        if key in market_cap.lower():
            num, multiplier_word = market_cap.split(key, 1)
            return float(num) * multipliers[key]
        
    return float(market_cap)
    
# Function to scrape S&P 500 ticker symbols from a webpage
def get_sp500_tickers():
    url = 'https://www.slickcharts.com/sp500'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')
    headers = [header.text for header in rows[0].find_all('th')]
    data = []

    for row in rows[1:]:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])

    df = pd.DataFrame(data, columns=headers)
    symbols = df['Symbol'].tolist()
    filtered_symbols = [symbol.replace('.', '-') for symbol in symbols if not any(char.isdigit() for char in symbol)]
    return filtered_symbols

# Function to scrape and return the total market capitalization
def get_total_market_cap():
    url = 'https://www.slickcharts.com/sp500/marketcap'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        market_cap_element = soup.find('h2', class_='text-center')
        
        if market_cap_element:
            return convert_text(market_cap_element.text.strip())
        else:
            print("Market cap element not found")
    else:
        print("Failed to retrieve the webpage: ", response.status_code)

# Main script execution starts here
number_of_tickers = get_argument()
sp500_tickers = get_sp500_tickers()
total_market_cap = get_total_market_cap()
stocks = yf.Tickers(sp500_tickers)  # Fetch financial data for S&P 500 tickers
market_caps = []
graph_market_caps = 0

# Iterate through the tickers and sum their market caps
for ticker in sp500_tickers[:number_of_tickers]:
    stock = stocks.tickers[ticker]

    try:
        market_cap = stock.info['marketCap']
        graph_market_caps += market_cap
        market_caps.append((ticker, market_cap))
    except:
        continue

# Add remaining market cap as 'Other'
market_caps.append(("Other", total_market_cap - graph_market_caps))

# Sort stocks by market cap
sorted_stocks = sorted(market_caps, key=lambda x: x[1], reverse=True)

# Prepare data for the pie chart
labels = [stock[0] for stock in sorted_stocks]
values = [stock[1] for stock in sorted_stocks]

# Create a pie chart
fig, ax = plt.subplots(figsize=(10, 6))
plt.title('Market Capitalization of the S&P 500', fontsize=16)
colors = cm.viridis(np.linspace(0, 1, len(values)))
explode = [0.1 if v >= max(values) * 0.2 else 0 for v in values]
font = fm.FontProperties(family='DejaVu Sans', size=10)
text_border = [path_effects.withStroke(linewidth=3, foreground='black')]

# Configure pie chart aesthetics
ax.pie(
    values,
    labels=labels,
    autopct='%1.1f%%',
    colors=colors,
    explode=explode,
    textprops=dict(fontproperties=font, path_effects=text_border, color='white'),
    labeldistance=0.6,
    pctdistance=0.8
)

# Add a white circle in the middle for aesthetics
center_circle = plt.Circle((0, 0), 0.50, fc='white')
fig.gca().add_artist(center_circle)

# Total market capitalization of displayed tickers
market_cap_total = ('{:,}'.format(int(total_market_cap)))
plt.figtext(0.5, 0.1,
            "Total Market Capitalization (Approx.) : " + str(market_cap_total),
            wrap=True, horizontalalignment='center', fontsize=12)

top_companies = ('{:,}'.format(int(graph_market_caps)))
plt.figtext(0.5, 0.075,
            "Combined Market Capitalization of Displayed Tickers (Approx.) : " + str(top_companies),
            wrap=True, horizontalalignment='center', fontsize=12)

plt.figtext(0.5, 0.05,
            "Number of Tickers Displayed " + str(number_of_tickers),
            wrap=True, horizontalalignment='center', fontsize=12)

# Ensure pie chart is a circle (not oval)
ax.axis('equal')
plt.legend(labels, loc='best', bbox_to_anchor=(1, 0.5))
plt.show()