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
    
    # update stock data with current prices
    for symbol in stockData:
        print(symbol)
        exchange = stockData[symbol]['exchange']

        if exchange != 'manual':
            quote = stockquotes.get_quote(symbol, exchange)
            stockData[symbol]['price'] = quote
            print(stockData[symbol]['price'])
            time.sleep(0.25)

    exchange_rate = stockquotes.get_exchange_rate('USD')
    
    # write the new stock data back to the file
    create_backup(filename) # backup before doing any writing
    readexcel.write(filename, stockData, exchange_rate)
