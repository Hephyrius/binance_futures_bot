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
    try:
        client.change_initial_leverage(_market, _leverage)
        client.change_margin_type(_market, _margin_type)
    except Exception as e:
        print(e)

def get_orders(client, _market="BTCUSDT"):
    orders = client.get_open_orders(_market)
    return orders, len(orders)

def get_positions(client):
    positions = client.get_position_v2()
    return positions

def get_specific_positon(client, _market="BTCUSDT"):
    positions = get_positions(client)
    
    for position in positions:
        if position.symbol == _market:
            break
    
    return position

def close_position(client, _market="BTCUSDT"):
    position = get_specific_positon(client, _market)
    qty = position.positionAmt
    
    _side = "BUY"
    if qty > 0.0:
        _side = "SELL"
    
    if qty < 0.0:
        qty = qty * -1
    
    execute_order(client, _market=_market,
                  _qty = qty,
                  _side = _side)
    

def execute_order(client, _market="BTCUSDT", _type = "MARKET", _side="BUY", _position_side="BOTH", _qty = 1.0):
    client.post_order(symbol=_market,
                      ordertype=_type,
                      side=_side,
                      positionSide=_position_side,
                      quantity = _qty)

def calculate_position_size(client, usdt_balance=1.0, _market="BTCUSDT", _leverage=1):
    price = client.get_symbol_price_ticker(_market)
    price = price[0].price
    
    qty = (int(usdt_balance) / price) * _leverage
    qty = qty * 0.99
    
    return qty
    
def get_market_precision(client, _market="BTCUSDT"):
    
    market_data = client.get_exchange_information()
    precision = 8
    for market in market_data.symbols:
        if market.symbol == _market:
            precision = market.quantityPrecision
            break
    return precision

def round_to_precision(_qty, _precision):
    new_qty = str(_qty).split(".")[1][:_precision]
    new_qty = str(_qty).split(".")[0] + "." + new_qty
    return float(new_qty)
#%%     Strategy codes



#%%

market = "BNBUSDT"
leverage = 1
margin_type = "CROSS"
#usdt = get_futures_balance(client, _asset = "USDT")
#initialise_futures(client, _market=market)

#qty = calculate_position_size(client, usdt_balance=usdt, _market=market)
#precision = get_market_precision(client, _market=market)

#qty = round_to_precision(qty, precision)

#execute_order(client, _qty=qty, _side="SELL" , _market=market)

#close_position(client, _market="BNBUSDT")



client.get_candlestick_data("BNBUSDT", interval="5m")



