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

import os

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


from alpha_vantage.timeseries import TimeSeries

def get_quote_alphavantage(symbol):
    ts = TimeSeries(key=os.getenv('ALPHAVANTAGE_API_KEY'))

    try:
        # Get json object with the intraday data and another with  the call's metadata
        data, meta_data = ts.get_intraday(symbol, interval='60min', outputsize='compact')
        #data, meta_data = ts.get_daily(symbol, outputsize='full')

        lastprice = data[meta_data['3. Last Refreshed']]['4. close']

    except KeyError:
        print('KeyError')
        raise KeyError


    return lastprice


def get_quote_google(symbol):
    from googlefinance.client import get_closing_data
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
    date = data['Data']['MarketData']['Daily']['TradeDate']

    return closerate,date

def get_quotes(symbol_list, exchange):
    # NOTE: not all symbols supported in a batch quote so returned list
    # may contain less than requested.
    if exchange != 'GOOG':
        raise RuntimeError('only GOOG is supported for a batch query')

    import asyncio
    from alpha_vantage.async_support.timeseries import TimeSeries
    import time
    import pandas as pd

    async def get_data(symbol):
        ts = TimeSeries(key=os.getenv('ALPHAVANTAGE_API_KEY'))
        ts.output_format = 'pandas'
        data, _ = await ts.get_quote_endpoint(symbol)
        await ts.close()
        return data

    loop = asyncio.get_event_loop()
    tasks = [get_data(symbol) for symbol in symbol_list]

    # create empty list of results
    result_list = []

    # divide list of tasks into chunks of 5 because alphavantage limits free account
    # to 5 stock requests per minute
    chunks = [tasks[x:x + 5] for x in range(0, len(tasks), 5)]

    for chunk in chunks:
        start_time = time.time()
        group1 = asyncio.gather(*chunk)
        results = loop.run_until_complete(group1)
        result_list.extend(results)
        execution_time = time.time() - start_time
        # print(results)
        # only allowed 5 quotes per minute so need to wait. while waiting print dots to show we're not stuck
        while execution_time < 60:
            print(".", end ="")
            execution_time = time.time() - start_time
            time.sleep(1.5)
        print(".")

    # convert result_list into format expected - a pandas dataframe. each row has columns: 1.timestamp 2.symbol 3.price
    #   create dataframe from list
    df = pd.concat(result_list) # create dataframe from list
    #   remove columns not needed
    df.drop(['02. open', '03. high', '04. low', '06. volume', '08. previous close', '09. change', '10. change percent'], axis=1)
    df.rename(columns={'01. symbol': 'symbol', '05. price': 'price','07. latest trading day': 'latest trading day'}, inplace=True)
    #   reorder columns
    df = df[['latest trading day', 'symbol', 'price']]
    #   reset the row indices so that they are 0,1,2.... and not anything else
    df = df.reset_index(drop=True)
    # data is a pandas dataframe. each row has columns: 1.timestamp 2.symbol 3.price
    return df


def get_quote(symbol, exchange):
    date = None
    quote = None
    N = 3
    n_tries = 0
    while n_tries < N and quote is None:
        n_tries = n_tries + 1
        try:
            if exchange == 'GOOG':
                quote = get_quote_alphavantage(symbol)
            elif exchange == 'TASE':
                quote,date = get_quote_tase(symbol)
            else:
                raise Exception("option does not exist")
        except:
            print('get_quote failed....retrying....')
            time.sleep(10)
        

    return quote,date

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

    for i in range(1000):
        last = get_quote_alphavantage('MSFT')
        print(last)

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


    


