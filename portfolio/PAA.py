# encoding: utf-8
"""
Created on Sun Jan 29 13:10:57 2017

@author: Stuart

Implementation of Protective Asset Allocation (PAA) by Keller & Keuning
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2759734
"""

import numpy as np

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

# raw data
SPY=[2,3,4,5,6,7,8,9,8,7,6,5,4,3,2,1]
GOG=[2,3,4,5,3,7,8,9,8,7,6,5,4,5,4,5]
APL=[2,3,4,5,6,1,4,9,8,7,6,5,4,4,5,6]
IBM=[2,3,4,5,6,7,8,9,8,2,2,2,1,3,2,1]


# should be read in somehow
TA_125 = [1356.0, 1305.0, 1323.0, 1358.0, 1358.0, 1402.6, 1484.0, 1478.0, 1447.0, 1463.0, 1328.0, 1402.0, 1421, 1410.0, 1459.0]
TA_SME150 = [1038.0, 1000.6, 992.0, 981.8, 975.8, 957.4, 1017.3, 1034.3, 969.8, 977.0, 976.1, 946.9, 955, 967.7, 990.0]
TA_TECH = [2660.0, 2545.0, 2499.0, 2599.0, 2621.0, 2770.0, 2759.3, 2789.0, 2637.0, 2615.0, 2299.0, 2636.0, 2636.0, 2679, 2693.0]
TA_SP500 = [3694.4, 3578.8, 3597.3, 3707.5, 3689.4, 3826.1, 3948.2, 3953.8, 3680.6, 3748.0, 3428.0, 3662.0, 3801.0, 3855, 3998]
TA_STOX50 = [3334.3, 3232.3, 3450.7, 3364.1, 3357.4, 3489.2, 3359.8, 3368.9, 3121.1, 3175.0, 2985.0, 3136.0, 3288.0, 3368, 3517]
TA_NIKEI_YEN = [17220.0, 16940.0, 17820.0, 17530.0, 17700.0, 17830.0, 17770.0, 18400.0, 17290.0, 17610.0, 16480.0, 16680.0, 16790, 16860, 17430]

TA_PROP = [523.9, 510.4, 511.7, 507.0, 507.9, 499.3, 526.6, 530.5, 512.2, 506.3, 477.3, 512.1, 532.2, 561.1, 585.2]
TA_GOLD = [1083.0, 1103.4, 1110.7, 1102.0, 1075.0, 1050.0, 1033.5, 1009.5, 1062.8, 1080.0, 1127.4, 1124.0, 1118.0, 1098.5, 1081.0]
TA_COMMOD = [691.5, 698.5, 750.6, 752.5, 767.2, 768.3, 763.5, 764.2, 755.2, 674.1, 636.0, 669.8, 675.2, 679.4, 687.7]

TA_TELBOND20 = [332.8, 332.8, 334.2, 333.5, 335.4, 335.0, 338.6, 338.1, 334.6, 332.4, 330.4, 335.4, 338.7, 344.2, 346.41]
TA_TELBOND_GROWTH = [3528.5, 3494.9, 3514.6, 3495.8, 3493.5, 3465.0, 3539.1, 3540.4, 3514.2, 3485.9, 3395.7, 3444.7, 3512.52, 3550.8, 3581]
TA_BOND_LONG = [615.1, 622.3, 612.1, 614.9, 606.4, 605.8, 610.9, 608.7, 601.4, 598.9, 602.4, 616.1, 622.52, 630.0, 631.94]
TA_TELBOND_LONG = [3712.0, 3727.8, 3694.7, 3683.1, 3651.8, 3598.4, 3664.6, 3671.4, 3636.0, 3637.3, 3564.4, 3616.3, 3650.14, 3699.7, 3725.16]

# "risk-free" or crash protection assets
bonds = ['TA_TREASURY_LINK_5_10', 'TA_TREASURY_FIX_2_5']


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


portfolio_old = [Security('SPY', 'SPY', SPY, PERIOD),
             Security('GOG', 'GOG', GOG, PERIOD),
             Security('APL', 'APL', APL, PERIOD),
             Security('IBM', 'IBM', IBM, PERIOD)]


portfolio = [Security('TA_125', 'TA_125', TA_125, PERIOD),
             Security('TA_SME150', 'TA_SME150', TA_SME150, PERIOD),
             Security('TA_TECH', 'TA_TECH', TA_TECH, PERIOD),
             Security('TA_SP500', 'TA_SP500', TA_SP500, PERIOD),
             Security('TA_STOX50', 'TA_STOX50', TA_STOX50, PERIOD),
             Security('TA_NIKEI_YEN', 'TA_NIKEI_YEN', TA_NIKEI_YEN, PERIOD),
             Security('TA_PROP', 'TA_PROP', TA_PROP, PERIOD),
             Security('TA_GOLD', 'TA_GOLD', TA_GOLD, PERIOD),
             Security('TA_COMMOD', 'TA_COMMOD', TA_COMMOD, PERIOD),
             Security('TA_TELBOND20', 'TA_TELBOND20', TA_TELBOND20, PERIOD),
             Security('TA_TELBOND_GROWTH', 'TA_TELBOND_GROWTH', TA_TELBOND_GROWTH, PERIOD),
             Security('TA_BOND_LONG', 'TA_BOND_LONG', TA_BOND_LONG, PERIOD),
             Security('TA_TELBOND_LONG', 'TA_TELBOND_LONG', TA_TELBOND_LONG, PERIOD)]

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


