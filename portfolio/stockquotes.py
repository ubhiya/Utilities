# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 13:33:51 2017

@author: Stuart
"""
try:
    from urllib.request import Request, urlopen
except ImportError:  # python 2
    from urllib2 import Request, urlopen
    
import json, time

from googlefinance.client import get_closing_data

# http://www.hasolidit.com/kehila/threads/%D7%9E%D7%9E%D7%A9%D7%A7-api-%D7%9C%D7%A9%D7%9C%D7%99%D7%A4%D7%AA-%D7%A0%D7%AA%D7%95%D7%A0%D7%99%D7%9D-%D7%9E%D7%94%D7%91%D7%95%D7%A8%D7%A1%D7%94.4251/page-6


"""
Examples to get tase json
http://externalapi.bizportal.co.il/Mobile/m/help

http://externalapi.bizportal.co.il/Mobile/help

http://www.hasolidit.com/kehila/threads/%D7%9E%D7%9E%D7%A9%D7%A7-api-%D7%9C%D7%A9%D7%9C%D7%99%D7%A4%D7%AA-%D7%A0%D7%AA%D7%95%D7%A0%D7%99%D7%9D-%D7%9E%D7%94%D7%91%D7%95%D7%A8%D7%A1%D7%94.4251/page-5#post-104768
"""

#add = 'https://servicesm.tase.co.il/mayainterfaces/api/CompanyData/?CompanyId=000604'
#add = 'https://servicesm.tase.co.il/taseinterfaces/api/StockData/?StockId=00604611'

#with urllib.request.urlopen(add) as url:
#    data = json.loads(url.read().decode())
#    print(data)



def get_quote_google(symbol):
    # try different exchanges - not all symbols available on every exchange
    exchange = ["NYSE", "NYSEARCA", "NASDAQ", "OTCMKTS", "BATS"]
	
    for e in exchange:
        params = [{'q': symbol, 'x': e, }]
        # x is the exchange - Dow Jones ("INDEXDJX"), NYSE COMPOSITE ("INDEXNYSEGIS"), S&P 500 ("INDEXSP")

        # get closing data for last month and then select the last known price
        period = "1M"
        df = get_closing_data(params, period)
		
        if df.empty == False:
        # note: df contains both last price and date
			# iloc[-1] returns the last element in the list
            #print(df)
            lastprice = df[symbol].iloc[-1]
            return lastprice
    
def get_quote_tase(symbol):
    add = 'https://servicesm.tase.co.il/taseinterfaces/api/StockData/?StockId='
    add = add + symbol

    html = urlopen(add).read()#urllib.request.urlopen(add).read() # this is json
    #print(type(html))
    data=json.loads(html.decode('utf-8'))

    closerate = data['Data']['MarketData']['Daily']['CloseRate']

    return closerate

def get_quote(symbol, exchange):

    quote = None
    N = 3
    n_tries = 0
    while n_tries < N and quote is None:
        n_tries = n_tries + 1
        try:
            if exchange == 'GOOG':
                quote = get_quote_google(symbol)
            elif exchange == 'TASE':
                quote = get_quote_tase(symbol)
            else:
                raise Exception("option does not exist")
        except:
            print('get_quote failed....retrying....')
            time.sleep(3)
        

    return quote

def get_exchange_rate(currency='USD'):
    add = "http://externalapi.bizportal.co.il/Mobile/GetExchangeRates?Token=USD"

    html = urlopen(add).read()#urllib.request.urlopen(add).read() # this is json
    #print(type(html))
    data=json.loads(html.decode('utf-8'))

    for k in data:
        if k['CurrencyCode'] == currency:
            return k['Rate']

    return None

    
    
if __name__ == "__main__":
    last = get_quote_google('VNQ')
    print(last)

    last = get_quote_google('MSFT')
    print(last)

    last = get_quote_google('TCEHY')
    print(last)

    last = get_quote_google('INDA')
    print(last)
	
    quotes = get_quote("IBM", 'GOOG')
    print(quotes)

    # execute only if run as a script
    cr = get_quote_tase('00604611')

    a = {'symbol': '00604611', 'currency': 'ILS', 'skip':False}
    quote = get_quote('00604611', 'TASE')
    
    print(quote)


    

