# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 16:44:33 2017

@author: Stuart
"""

import readexcel, stockquotes
import time, os, shutil, datetime
import pandas as pd

def create_backup(filepath):
    destpath = filepath + '.bak'
    shutil.copy(filepath, destpath)
    
    modifiedTime = os.path.getmtime(destpath) 

    timeStamp =  datetime.datetime.fromtimestamp(modifiedTime).strftime("%b_%d_%y_%H%M%S")
    os.rename(destpath,destpath+"_"+timeStamp)


def file_to_open():
    import tkinter
    from tkinter.filedialog import askopenfilename

    tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing

    # show an "Open" dialog box and return the path to the selected file
    filename = askopenfilename(initialdir="./",
                               title="Select file",
                               filetypes=(("Ms-Excel files", "*.xls *.xlsx"), ("all files", "*.*")))
    print(filename)

    return filename

def create_symbol_list(stockData, exchange_required):
    # create tuple of symbols to query in one batch - foreign exchanges only google/alphavantage
    symbol_list = []
    for symbol in stockData:
        exchange = stockData[symbol]['exchange']
        if exchange == exchange_required:
            symbol_list.append(symbol)

    symbol_list = list(set(symbol_list))  # create unique list by converting to set and back to list (order not preserved)

    return symbol_list


if __name__ == "__main__":
    # execute only if run as a script
    filename = file_to_open()  #"C:\\Users\\Stuart\\Dropbox\\test\\Portfolio.xlsx"

    # read the current stock data
    stockData = readexcel.read(filename)

    # create tuple of unique symbols to query in one batch - and prefetch all quotes for symbols
    symbol_list_foreign = create_symbol_list(stockData, 'GOOG')
    symbol_list_tase = create_symbol_list(stockData, 'TASE')
    quotes_foreign = stockquotes.get_quotes(symbol_list_foreign, 'GOOG')
    quotes_tase = stockquotes.get_quotes_tase(symbol_list_tase)

    # create one dataframe for all pre-fetched symbols
    quotes = pd.concat([quotes_foreign, quotes_tase], ignore_index=True)

    # update stock data with current prices
    for symbol in stockData:
        print(symbol, end=':\t')
        exchange = stockData[symbol]['exchange']

        if (exchange == 'TASE') or (exchange == 'GOOG'):  # quotes already retrieved (see above)
            # could just pull out the row containing the symbol of interest using r = quotes.loc[quotes['symbol'] == symbol]
            index_list = quotes.index[quotes['symbol'] == symbol].tolist()
            if len(index_list) > 0:
                index = index_list[0]
                quote = quotes.loc[index]['price']  # Series from column
                date = quotes.loc[index]['latest trading day']
            else:
                try:
                    quote, date = stockquotes.get_quote(symbol, exchange)
                except KeyError:
                    print('QUOTE UNAVAILABLE - UNCHANGED', end=':\t')
                    quote = stockData[symbol]['price']  # NOTE - UNCHANGED
                    date = stockData[symbol]['date']

            stockData[symbol]['price'] = quote
            stockData[symbol]['date'] = date

        print(stockData[symbol]['price'])
        time.sleep(0.25)


    exchange_rate = stockquotes.get_exchange_rate('USD')
    
    # write the new stock data back to the file
    create_backup(filename) # backup before doing any writing
    readexcel.write(filename, stockData, exchange_rate)
