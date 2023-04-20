from pymongo import MongoClient
import pandas as pd
import numpy as np
import ccxt
import time
import json

class GridBot_Classic:
    def __init__(self, params = {}):
        self.n_grids = params['n_grids'] + 1
        self.k_delta = params['k_delta']
        self.r_epsilon = params['r_epsilon']
        self.start_time = int(time.time()*1000)

    def set_market(self, symbol):
        symbol = symbol
        self.db_client = MongoClient('localhost')
        self.db = self.db_client['BINANCE_FUTURES']
        self.market_data = self.db['SYMBOL_INFO'].find_one({'symbol':symbol})
        self.epsilon_min = self.market_data['minNotional']
        self.delta_min = self.market_data['minStep']
        self.size = self.r_epsilon * self.epsilon_min
        self.distance = self.k_delta * self.delta_min

    def is_available(self, symbol, price):
        db = self.db
        cursor = db['ACTIVE_ORDERS']
        query = {"s":symbol.replace('/', ''),
        "p":{"$gt":float(price - self.distance), "$lt":float(price + self.distance)},
        }
        active_order = list(cursor.find(query))

        if len(active_order) > 0:
            return False
        return True

    def cancel_orders(self, symbol, range_orders):
        cursor = self.db['ACTIVE_ORDERS']
        query = {
        "s":symbol.replace('/', ''),
        "$or":[{"p":{"$gt":float(range_orders[1])}} , {"p":{"$lt":float(range_orders[0])}}],
        }


        # Buscar tambien si en un ancho de grid hay mas de dos ordenes.
        cancel_orders = list(cursor.find(query))

        # cancel_orders = pd.DataFrame(list(cursor.find(query))).to_dict('records')

        print(cancel_orders)
        print(range_orders)
        return cancel_orders

    def get_orders(self, symbol):
        self.set_market(symbol)
        midprice = self.db['SYMBOL_INFO'].find_one( {'symbol':symbol})['midprice']
        range_orders = (midprice - (self.distance * self.n_grids), midprice + (self.distance * self.n_grids))
        new_orders = []

        midprice_buy = midprice
        midprice_sell = midprice

        cursor = self.db['USER_INFO']
        position = list(cursor.find({'symbol':symbol}).sort("_id",-1).limit(1))

        if len(position) > 0:
            if float(position['a']['P'][0]['pa']) < 0:
                midprice_buy = float(position['a']['P'][0]['ep'])
            elif float(position['a']['P'][0]['pa']) > 0:
                midprice_sell = float(position['a']['P'][0]['ep'])


        for i in range(1, self.n_grids):

            buy_price = midprice_buy - i*self.distance

            if self.is_available(symbol, buy_price) and (buy_price < midprice_buy):
                buy_order = {
                'symbol':symbol,
                'type':'limit',
                'side':'buy',
                'quantity':self.size,
                'price':buy_price,
                'params':{
                "time_in_force":'PostOnly',
                    }
                }
                new_orders.append(buy_order)

            sell_price = midprice_sell + i*self.distance

            if self.is_available(symbol, sell_price) and (sell_price > midprice_sell):
                sell_order = {
                'symbol':symbol,
                'type':'limit',
                'side':'sell',
                'quantity':self.size,
                'price':sell_price,
                'params':{
                "time_in_force":'PostOnly',
                    }
                }
                new_orders.append(sell_order)
        return new_orders, self.cancel_orders(symbol, range_orders)
