import ccxt
import pandas as pd
import numpy as np
import json
from datetime import datetime
from pymongo import MongoClient


apikeyProduction = '0gXMyPphJJoOhPlgEKDyUdBjYjwsufrlVBkdMKT7adznsE3j22aREo1FcyPxS2AQ'
secretProduction = 'kJrk9nVvMMZ4XV80M5QZj9SvJFUpmbmiNNjSh9mIZbL5cAdUM3WntJibIdEAyTr8'

def update_markets(exchange, leverage = 5, marginType = 'ISOLATED'):
    client = MongoClient('localhost')
    db = client['BINANCE_FUTURES']
    cursor = db['SYMBOL_INFO']
    markets = exchange.fetch_markets()
    # print(markets)
    in_db = pd.DataFrame(list(cursor.find()))
    temp = []

    if len(in_db) != 0:
        temp = list(in_db['symbol'])


    for market in markets:
        symbol = market['symbol']
        # print(json.dumps(market, indent = 2))
        if 'pricePrecision' in market['info']:
            min_notional = market['info']['filters'][5].get('notional', None)
            if min_notional is not None:
                min_notional = float(min_notional)
            
            symbol_info = {
            'symbol' : symbol,
            'pricePrecision': int(market['info']['pricePrecision']),
            'quantityPrecision': int(market['info']['quantityPrecision']),
            'minNotional': min_notional,
            'minStep': float(1/10**int(market['info']['pricePrecision'])),
            'bid':0,
            'ask':0,
            'midprice':0,
            }

            if len(in_db) == 0 and market['linear']:
                # print(json.dumps(market, indent = 2 ))
                cursor.insert_one(symbol_info)

            else:

                if symbol in temp:
                    query = {'symbol': symbol}
                    update = {'$set': symbol_info}
                    cursor.update_one(query, update)
                    temp.remove(symbol)
                else:
                    cursor.insert_one(symbol_info)

    if len(temp) != 0:
        for symbol in temp:
            query = {'symbol':symbol}
            cursor.delete_one(query)

    markets = exchange.fapiPrivateGetPositionRisk()

    for market in markets:
        symbol = market['symbol']
        # print(market)
        if (float(market['leverage']) != leverage):
            exchange.fapiPrivate_post_leverage({
            "symbol":symbol,
            "leverage":leverage
            })

        if(market['marginType'] != marginType.lower()):
            exchange.fapiPrivate_post_margintype({
            "symbol":symbol,
            "marginType":marginType
            })

    print('Collections create succesfully')

exchange = ccxt.binance({
        'apiKey': apikeyProduction,
        'secret': secretProduction,
        'enableRateLimit':True,
        'timeout':3000,
        'options': {
            'defaultType': 'future',
        }
        })

update_markets(exchange)
