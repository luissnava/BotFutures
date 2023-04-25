
import sys
sys.path.append("../")

import pandas as pd
import numpy as np
import ccxt
from pymongo import MongoClient

from multiprocessing import Process
import threading
import time

from database import update_database
from markets import update_markets
from orders import update_orders
from webdata import run_websocket

from GridBot import GridBot_Classic

import traceback

apikeyProduction = '0gXMyPphJJoOhPlgEKDyUdBjYjwsufrlVBkdMKT7adznsE3j22aREo1FcyPxS2AQ'
secretProduction = 'kJrk9nVvMMZ4XV80M5QZj9SvJFUpmbmiNNjSh9mIZbL5cAdUM3WntJibIdEAyTr8'

class BotController:
    def __init__(self, symbols, strategy):
        self.symbols = symbols
        self.strategy = strategy
        self.exchange = ccxt.binance({
                'apiKey': apikeyProduction,
                'secret': secretProduction,
                'enableRateLimit':True,
                'timeout':3000,
                'options': {
                    'defaultType': 'future',
                }
                })

    def bot_runner(self):
        websymbols = [(symbol.replace('/USDT', 'USDT').lower()) for symbol in self.symbols]
        p = Process(target = run_websocket, args = (websymbols, ['depth5']))
        p.start()
        print('1')
        time.sleep(3)
        print('2')

        while True:
            try:
                print('im working')
                update_database()
                for symbol in self.symbols:
                    new_orders, cancel_orders = self.strategy.get_orders(symbol = symbol)
                    update_orders(exchange = self.exchange, new_orders = new_orders, cancel_orders = cancel_orders)

            except Exception as e:
                print(e)
                traceback.print_exc()


db_client = MongoClient('localhost')
db = db_client['BINANCE_FUTURES']
cursor = db['SYMBOL_INFO']
symbol_info = pd.DataFrame(list(cursor.find()))
# print(symbol_info)
symbol = symbol_info['symbol']

symbol = ['ADA/USDT:USDT']


params = {
    'strategy_name':'GridBotClassic',
    'n_grids':20,
    'k_delta':150,
    'r_epsilon':1.1,
}


strategy = GridBot_Classic(params = params)
model = BotController(symbols = symbol, strategy = strategy)
model.bot_runner()
