# PoloTrader
CryptoCurrency trader using Python, NumPy, and Pandas on the Poloniex exchange

Right now the code just analyzes the data, while in the future I would like to make decisions and trade on this analysis.
Here's what it does:
- Grabs the list of currencies
- Gets the candlestick data for the last 24 hours for each currency
- Normalizes candlestick data for easier comparison
- Finds the 3 currencies with the largest return in the last 24 hours
- Uses Twilio to send a text message with this data
- Also sends an email with the graphs of those 3 currency's prices as well as Bollinger Band data and Rolling Mean
