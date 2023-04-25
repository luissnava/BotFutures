
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
from pymongo import MongoClient
import pandas as pd
import numpy as np
import threading
import time
import json
import os
import sys


apikeyProduction = '0gXMyPphJJoOhPlgEKDyUdBjYjwsufrlVBkdMKT7adznsE3j22aREo1FcyPxS2AQ'
secretProduction = 'kJrk9nVvMMZ4XV80M5QZj9SvJFUpmbmiNNjSh9mIZbL5cAdUM3WntJibIdEAyTr8'


def update_mid_price(symbol, new_ask = None, new_bid = None):
    db_client = MongoClient('localhost')
    db = db_client['BINANCE_FUTURES']
    cursor = db['SYMBOL_INFO']
    query = {'symbol':symbol}
    if not np.isnan(new_ask):
        update = {'$set':{'ask':new_ask}}
        cursor.update_one(query, update)

    if not np.isnan(new_bid):
        update = {'$set':{'bid':new_bid}}
        cursor.update_one(query, update)

    symbol_info = pd.DataFrame(list(cursor.find(query)))

    ask = symbol_info['ask'][0]
    bid = symbol_info['bid'][0]
    midprice = (ask+bid)/2

    update = {'$set':{'midprice':midprice}}
    cursor.update_one(query,update)


def fix_floats(data):
    if isinstance(data,list):
        iterator = enumerate(data)
    elif isinstance(data,dict):
        iterator = data.items()
    else:
        raise TypeError("can only traverse list or dict")

    for i,value in iterator:
        if isinstance(value,(list,dict)):
            fix_floats(value)
        elif isinstance(value,str):
            try:
                data[i] = float(value)
            except ValueError:
                pass
    return data

def print_stream(ws):

    db_client = MongoClient('localhost')
    db = db_client['BINANCE_FUTURES']
    cursor = db['LOGGER']

    while True:
        if ws.is_manager_stopping():
            exit(0)
        new_data = ws.pop_stream_data_from_stream_buffer()
        if new_data is False:
            time.sleep(0.01)
        else:
            new_data = json.loads(new_data)
            if 'stream' in new_data:
                if 'depthUpdate' in new_data['data'].values():
                    symbol = new_data['data']['s']
                    ask = float(new_data['data']['a'][0][0])
                    bid = float(new_data['data']['b'][0][0])
                    update_mid_price(symbol.replace('USDT', '/USDT'), ask, bid)

            elif 'ORDER_TRADE_UPDATE' in new_data.values():
                if new_data['o']['X'] != 'PARTIALLY_FILLED':
                    new_data['o']['type'] = 'order'
                    new_data = fix_floats(new_data['o'])
                    cursor.insert_one(new_data)
            elif 'ACCOUNT_UPDATE' in new_data.values():
                new_data['type'] = 'position'
                cursor.insert_one(new_data)


def run_websocket(symbols, channels):
    ws = BinanceWebSocketApiManager(exchange="binance.com-futures")
    ws.create_stream(["arr"], ["!userData"], api_key=apikeyProduction, api_secret=secretProduction, stream_label = "UserData")
    ws.create_stream(channels, symbols)
    worker_thread = threading.Thread(target=print_stream, args=(ws,))
    worker_thread.start()

    while True:
        ws.print_summary()
        time.sleep(1)
        # os.system("clear")

# symbols = ['ltcusdt']
# channels = ['depth5']
# run_websocket(symbols = symbols, channels = channels)
