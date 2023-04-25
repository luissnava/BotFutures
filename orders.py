
import ccxt
import time
import pandas as pd
import json
import time
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor

def format_price_and_amount(symbol, price, amount):
    
    db_client = MongoClient('localhost')
    db = db_client['BINANCE_FUTURES']
    cursor = db['SYMBOL_INFO']
    query = {"symbol":symbol}
    symbol_info = pd.DataFrame(list(cursor.find(query)))
    amount = round(amount, int(symbol_info['quantityPrecision'].iloc[0]))
    price = round(price, int(symbol_info['pricePrecision'].iloc[0]))
    return price, amount

def update_orders(exchange, new_orders = [], cancel_orders = []):
    
    # print(json.dumps(new_orders, indent = 2 ))
    executor = ThreadPoolExecutor(max_workers = 5)
    for order in new_orders:
        result = executor.submit(create_order, exchange, order)
        print(result.result())

    for order in cancel_orders:
        result = executor.submit(cancel_order, exchange, order)
        print(result.result())

    time.sleep(1)

def create_order(exchange, params_order):
    price, amount = format_price_and_amount(symbol = params_order['symbol'], price = params_order['price'], amount = params_order['quantity']/params_order['price'])
    order = exchange.create_order(
        symbol = params_order['symbol'],
        type = params_order['type'], # 'market', 'limit'
        side = params_order['side'], # 'buy', 'sell'
        price = price,
        amount = amount,
        params = params_order['params']
    )


def cancel_order(exchange, params_order = {}):
    exchange.cancel_order(symbol = params_order['s'].replace('USDT', '/USDT'), id = int(params_order['i']))
