# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 16:44:33 2017

@author: Stuart
"""

import readexcel, stockquotes
import time, os, shutil, datetime

def create_backup(filepath):
    destpath = filepath + '.bak'
    shutil.copy(filepath, destpath)
    
    modifiedTime = os.path.getmtime(destpath) 

    timeStamp =  datetime.datetime.fromtimestamp(modifiedTime).strftime("%b_%d_%y_%H%M%S")
    os.rename(destpath,destpath+"_"+timeStamp)


if __name__ == "__main__":
    # execute only if run as a script
    filename = "C:\\Users\\Stuart\\Dropbox\\test\\Portfolio.xlsx"

    # read the current stock data
    stockData = readexcel.read(filename)


    # create tuple of symbols to query in one batch - foreign exchanges only google/alphavantage
    symbol_list = []
    for symbol in stockData:
        exchange = stockData[symbol]['exchange']
        if exchange == 'GOOG':
            symbol_list.append(symbol)

    # prefetch all quotes for symbols that alphavantage supports.
    quotes = stockquotes.get_quotes(symbol_list, 'GOOG')


    # update stock data with current prices
    for symbol in stockData:
        print(symbol, end=':\t')
        exchange = stockData[symbol]['exchange']

        if exchange != 'manual':
            if exchange == 'GOOG': # quotes already retrieved (see above)
                index_list = quotes.index[quotes['1. symbol'] == symbol].tolist()
                if len(index_list) > 0:
                    index = index_list[0]
                    quote = quotes.loc[index]['2. price']  # Series from column
                    date = quotes.loc[index]['4. timestamp']
                else:
                    try:
                        quote,date = stockquotes.get_quote(symbol, exchange)
                    except KeyError:
                        print('QUOTE UNAVAILABLE - UNCHANGED', end=':\t')
                        quote = stockData[symbol]['price'] #NOTE - UNCHANGED
                        date = stockData[symbol]['price']

            else:
                quote,date = stockquotes.get_quote(symbol, exchange)

            stockData[symbol]['price'] = quote
            stockData[symbol]['date'] = date

        print(stockData[symbol]['price'])
        time.sleep(0.25)


    exchange_rate = stockquotes.get_exchange_rate('USD')
    
    # write the new stock data back to the file
    create_backup(filename) # backup before doing any writing
    readexcel.write(filename, stockData, exchange_rate)
