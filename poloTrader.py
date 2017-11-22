"""Analyze a portfolio."""

from poloWrapper import poloniex
from twilioWrapper import twilio as tw
import pandas as pd
import numpy as np
import json, csv
import sched, time, datetime as dt
import matplotlib.pyplot as plt
import smtplib as smtp
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Creating an instance of the Polo class with our secrets.json file
with open("secrets.json") as secrets_file:
    secrets = json.load(secrets_file)
    secrets_file.close()
    polo = poloniex(secrets['poloniexKey'], secrets['poloniexSecret'])

# Twilio secret variables
AccountSID = secrets['twilioKey']
AuthToken = secrets['twilioSecret']
MyNumber = secrets['myNumber']
TwilioNumber = secrets['twilioNumber']

# Email values
MY_ADDRESS = secrets['myEmail']
PASSWORD = secrets['emailSecret']

TIMER = 600
# Boolean values
PLOT_DATA = True
REPEATE_SCRIPT = True
SEND_SMS = True
SEND_EMAIL = True
VERBOSE = False

def analyzeVolume():
	# polo = poloniex(APIKey, Secret)
	volume = pd.DataFrame(polo.return24Volume())

def setCurrencyList():
	# polo = poloniex(APIKey, Secret)
	currencyList = pd.DataFrame(polo.return24Volume())
	currencyList = pd.DataFrame(currencyList.index.tolist(), columns=['Currencies'])
	currencyList = "BTC_" + currencyList
	# Delete BTC_BTC and BTC_USDT
	currencyList = currencyList[currencyList.Currencies != "BTC_BTC"]
	currencyList = currencyList[currencyList.Currencies != "BTC_USDT"]
	return currencyList

def analyzeChart():
	# polo = poloniex(APIKey, Secret)
	timestamp = int(time.time())
	currencyList = setCurrencyList()

	# Get dates and first currency data, massage data into something usable
	prices = get_close_chart(currencyList.iloc[0,0], timestamp)
	print currencyList.iloc[0][0]
	currencyList.drop(currencyList.index[0], inplace=True)
	frames = [prices]
	if VERBOSE : prices.to_csv('prices.csv')

	for currency in currencyList["Currencies"]:
		print currency
		dataframe = get_close_chart(currency, timestamp)
		frames.append(dataframe)
	frames[0].to_csv('frame.csv')
	result = pd.concat(frames, axis=1)
	result.reset_index(drop=True)
	result.fillna(method="ffill", inplace=True)
	result.fillna(method="bfill", inplace=True)
	if VERBOSE : result.to_csv('result.csv')

	normed_vals = result/result.iloc[0]
	print time.strftime('%-m/%-d/%y %-I:%M', time.localtime(timestamp))
	maxCoins, text = get_max_close(normed_vals)
	dfs = []
	for coin in maxCoins:
		dfs.append(get_close_chart(coin, timestamp))

	if VERBOSE : df.to_csv('df.csv')

	# Reporting
	if PLOT_DATA: plot_data(dfs, maxCoins, timestamp)
	if SEND_SMS: send_sms(text)
	if SEND_EMAIL: send_email(text, maxCoins, timestamp)
	if REPEATE_SCRIPT: set_timer(analyzeChart)

# How to call:
# cr, adr, sddr, sr = compute_portfolio_stats(normed_vals = normed_vals)
# print cr, adr, sddr, sr
def compute_portfolio_stats(normed_vals, rfr = 0, sf = 252):
	"""Return portfolio stats, using values"""
	portfolio_vals = normed_vals.sum(axis=1)
	daily_returns = (portfolio_vals[1:] / portfolio_vals[:-1].values) - 1

	cr = (portfolio_vals.iloc[-1]/portfolio_vals.ix[0]) - 1
	adr = daily_returns.mean()
	sddr = abs(np.std(daily_returns, ddof=1))
	sr = np.sqrt(252) * ((daily_returns).mean()/daily_returns.std(ddof=1))
	
	return cr, adr, sddr, sr
	
def get_max_close(normed_vals):
	if VERBOSE : normed_vals.to_csv('normed_vals.csv')
	# maxCoin = normed_vals[-1:].idxmax(axis=1)[0]
	order = np.argsort(-normed_vals.values, axis=1)[-1:, :3][0]
	maxCoins = []
	maxCoins.append(normed_vals.columns[order[0]])
	maxCoins.append(normed_vals.columns[order[1]])
	maxCoins.append(normed_vals.columns[order[2]])
	text1 = "Largest return: "     + maxCoins[0] + " with " + str((round(normed_vals.ix[-1:,maxCoins[0]][0], 8) - 1) * 100) + " percent return"
	text2 = "2nd Largest return: " + maxCoins[1] + " with " + str((round(normed_vals.ix[-1:,maxCoins[1]][0], 8)- 1) * 100) + " percent return"
	text3 = "3rd Largest return: " + maxCoins[2] + " with " + str((round(normed_vals.ix[-1:,maxCoins[2]][0], 8) - 1) * 100) + " percent return"
	text = text1 + "\n" + text2 + "\n" + text3
	print text
	return maxCoins, text

def get_rolling_mean(values, window = 20):
	"""Return rolling mean of given values, using specified window size."""
	return values.rolling(window, center=False).mean()


def get_rolling_std(values, window = 20):
	"""Return rolling standard deviation of given values, using specified window size."""
	return values.rolling(window, center=False).std()


def get_bollinger_bands(rm, rstd, degrees):
	"""Return upper and lower Bollinger Bands."""
	upper_band = rm + rstd * degrees
	lower_band = rm - rstd * degrees
	return upper_band, lower_band

def send_sms(message):
	"""Send sms to myself using Twilio"""
	twilio = tw(AccountSID, AuthToken, MyNumber, TwilioNumber)
	twilio.send_sms(message)

def send_email(message, maxCoins, timestamp):
	server   = smtp.SMTP('smtp.gmail.com:587')
	# create a message
	msg      = MIMEMultipart()
	text     = MIMEText(message)
	subject = time.strftime('%-m/%-d/%y %-I:%M', time.localtime(timestamp))

	for coin in maxCoins:
		fileid = time.strftime('%Y%m%d%H%M%S', time.localtime(timestamp))
		img_data = open("graphs/%s_%s.png"%(fileid, coin), 'rb').read()
		image    = MIMEImage(img_data, name="%s_%s.png"%(fileid, coin))
		msg.attach(image)
	msg['Subject'] = "crypto - " + subject
	msg.attach(text)

	# Set up server
	server.ehlo()
	server.starttls()
	server.login(MY_ADDRESS, PASSWORD)
	server.sendmail(MY_ADDRESS, MY_ADDRESS, msg.as_string())
	# Terminate the SMTP session and close the connection
	server.quit()
 
def set_timer(onFire):
	schedule = sched.scheduler(time.time, time.sleep)
	schedule.enter(TIMER, 1, onFire, ())
	schedule.run()

def plot_data(dfs, maxCoins, timestamp):
	i = 0
	for coin in maxCoins:
		# Get rolling measurements, and Bollinger Bands
		rstd = get_rolling_std(dfs[i][coin], window=20)
		rm = get_rolling_mean(dfs[i][coin], window=20)
		upper_band, lower_band = get_bollinger_bands(rm, rstd, 1 )
		upper_band2x, lower_band2x = get_bollinger_bands(rm, rstd, 2)

		# Plot raw maxCoin close values, rolling mean and Bollinger Bands
		fig = plt.figure()
		ax = dfs[i][coin].plot(title="Bollinger Bands", label=coin)
		ax = rm.plot(title= coin, label='rolling mean')
		# upper_band.plot(label='upper band', ax=ax)
		upper_band2x.plot(label='upper band2x', ax=ax)
		# lower_band.plot(label='lower band', ax=ax)
		lower_band2x.plot(label='lower band2x', ax=ax)

		# Add axis labels and legend and plot
		ax.set_xlabel("Date")
		fig.autofmt_xdate()
		fig.tight_layout()
		ax.set_ylabel("Price")
		ax.legend(loc='best')
		plt.autoscale()
		# plt.show()
		fileid = time.strftime('%Y%m%d%H%M%S', time.localtime(timestamp))
		plt.savefig('graphs/%s_%s.png'%(fileid, coin))
		i+=1

def get_close_chart(coin, timestamp):
	# polo = poloniex(APIKey, Secret)
	# Get chart data for the coin's close prices, clean it up a little and return
	df = pd.DataFrame(polo.returnChartData(coin, timestamp - 86400, timestamp, '300'))
	df['date'] = pd.to_datetime(df["date"], unit='s')
	df.set_index(['date'], inplace=True)
	df = df.tz_localize('UTC').tz_convert('America/New_York')
	df.index = df.index.strftime('%-m/%-d/%y %-H:%M')
	df = df[['close']]
	df.rename(columns={"close": coin}, inplace=True)
	return df

if __name__ == "__main__":
	analyzeChart()


