# encoding: utf-8
"""
Created on Sun Jan 29 13:10:57 2017

@author: Stuart

Implementation of Protective Asset Allocation (PAA) by Keller & Keuning
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2759734
"""

import numpy as np
import pandas as pd

# moving average period ie. lookback
PERIOD = 10

# maximal number of risk assets in portfolio
TOP = 6

# define protection factor (a)
protection_factor = 2

print('-------------------------------------------------')
print('protection factor: {0}'.format(protection_factor))
print('lookback period  : {0}'.format(PERIOD))
print('-------------------------------------------------')

filename = "C:\\Users\\Stuart\\Dropbox\\Finance\\data.xlsx"
xl = pd.ExcelFile(filename)
xl.sheet_names
df = xl.parse("data")
df.head()

# "risk-free" or crash protection assets
bonds = ['TA_TREASURY_LINK_5_10', 'TA_TREASURY_FIX_2_5']

# "risk" part of portfolio
# NOTE: symbols should be read from same excel file
symbols = ['TA_125', 'TA_SME150', 'TA_TECH', 'TA_SP500', 'TA_STOX50', 'TA_NIKEI_YEN', 'TA_PROP',
           'TA_GOLD', 'TA_COMMOD', 'TA_TELBOND20', 'TA_TELBOND_GROWTH', 'TA_BOND_LONG', 'TA_TELBOND_LONG']

def moving_average(data_set, periods=3):
    weights = np.ones(periods) / periods
    return np.convolve(data_set, weights, mode='valid')

# test moving average
data = [1, 2, 3, 6, 9, 12, 20, 28, 30, 25, 22, 20, 15, 12, 10]
ma = moving_average(np.asarray(data), 3)
assert (np.around(ma, decimals=2)==np.array([2.0, 3.67, 6.0, 9.0, 13.67, 20.0, 26.0, 27.67, 25.67, 22.33, 19.0, 15.67, 12.33])).all() == True

def momentum(data_set, price, period):
    # MOM(L) = p0/SMA(L) - 1

    m = moving_average(data_set, period)
    l = len(m)
    sma = m[l-1]

    mom = price/sma - 1

    return mom

#ma2=moving_average(np.asarray(SPY), 5)
#print(ma2)

#mom = momentum(np.asarray(SPY), 5,5)
#print(mom)

def bond_fraction(N,n,a=2):
    #BF = (N-n)/(N-n1), with n1 = a*N/4,
    n1 = a*N/4
    bf = (N-n)/(N-n1)

    if n<=n1:
        bf = 1

    return bf


class Security(object):
    def __init__(self, name, symbol, data, period=5):
        self.name = name
        self.symbol = symbol

        # historical data is all except the last price
        self.data = np.asarray(data[0:len(data)-1])

        # current price is the last one
        self.price = data[len(data)-1]

        # calculate momentum
        self.momentum = momentum(self.data, self.price, period)

# build portfolio as list of Securitys
portfolio = []
for symbol in symbols:
    portfolio.append(Security(symbol, symbol, df[symbol].to_list(), PERIOD))

# sort by momentum with highest momentum first
portfolio.sort(key=lambda x: x.momentum, reverse=True)

# calculate number of 'good' risk assets
n = sum(p.momentum > 0 for p in portfolio)
print('risk assets with positive momentum: {0}'.format(n))

# define maximal number of risk assets in portfolio
top = min(TOP, n)
print('total risk assets in portfolio: {0}\n'.format(top))

# leave only the top of the portfolio for further consideration
portfolio_top = portfolio[:top]

# define protection factor
a = protection_factor

# calculate bond fraction
bf = bond_fraction(len(portfolio),n,a)

# risk assets fraction
sf = 1-bf


print('------- Suggested Portfolio ---------------------')
print('bond fraction:stock fraction {0:.2f}:{1:.2f}\n'.format(bf,sf))

print('risk')
for p in portfolio_top:
    if p.momentum > 0:
        print('     {0}: {1:.4f} (momentum={2:.1f}%)'.format(p.name, 1/top*sf, 100*p.momentum))

print('\nsafe')
n_bonds = len(bonds)
for b in bonds:
    print('     {0}: {1:.4f}'.format(b, 1/n_bonds*bf))


