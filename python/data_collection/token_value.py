'''
This file is to collect token values of each protocol.
https://www.coingecko.com/
'''

import pandas as pd

dir = 'token_history/'


# read values from csv and keep time and price
def readTokens(token):
    data = pd.read_csv(dir + token)
    data['time'] = data['snapped_at'].str[0:10]
    values = data[['time', 'price']]
    return values


if __name__ == '__main__':
    suffix = '-usd-max.csv'
    aave = readTokens('aave' + suffix)
    compound = readTokens('comp' + suffix)
    cream = readTokens('cream' + suffix)
    truefi = readTokens('tru' + suffix)
