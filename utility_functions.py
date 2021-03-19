from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

import json

#Load our credentials from json, instead of hard coding.
api_info = json.load(open ("keys.json", "r"))
api_key = api_info['api_key']
api_secret = api_info['api_secret']

#Connect to the binance api
client = RequestClient(api_key=api_key, secret_key=api_secret)



#Get futures balances. We are interested in USDT by default as this is what we use as margin.
def get_futures_balance(client, _asset = "USDT"):
    balances = client.get_balance()
    asset_balance = 0
    for balance in balances:
        if balance.asset == _asset:
            asset_balance = balance.balance
            break
    
    return asset_balance

#Init the market we want to trade. First we change leverage type
#then we change margin type
def initialise_futures(client, _market="BTCUSDT", _leverage=1, _margin_type="CROSSED"):
    client.change_initial_leverage(_market, _leverage)
    client.change_margin_type(_market, _margin_type)

def get_orders(client, _market="BTCUSDT"):
    orders = client.get_open_orders("btcusdt")
    
    return orders, len(orders)

#%%

market = "BTCUSDT"
leverage = 1
margin_type = "CROSS"
#usdt = get_futures_balance(client, _asset = "USDT")
#initialise_futures(client)
get_orders(client)