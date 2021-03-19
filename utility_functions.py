from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
import pandas as pd
import json
from finta import TA
import numpy as np
import matplotlib.pyplot as plt

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


def get_liquidation(client, _market="BTCUSDT"):
    position = get_specific_positon(client, _market)
    price = position.liquidationPrice
    return price

def get_entry(client, _market="BTCUSDT"):
    position = get_specific_positon(client, _market)
    price = position.entryPrice
    return price

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

def get_market_price(client, _market="BTCUSDT"):
    price = client.get_symbol_price_ticker(_market)
    price = price[0].price
    return price
    
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
def convert_candles(candles):
    o = []
    h = []
    l = []
    c = []
    v = []
    
    for candle in candles:
        o.append(float(candle.open))
        h.append(float(candle.high))
        l.append(float(candle.low))
        c.append(float(candle.close))
        v.append(float(candle.volume))
        
    return o, h, l, c, v
    

def construct_heikin_ashi(o, h, l, c):
    h_o = []
    h_h = []
    h_l = []
    h_c = []
    
    for i, v in enumerate(o):
        
        close_price = (o[i] + h[i] + l[i] + c[i]) / 4
        
        if i == 0:
            open_price = close_price
        else:
            open_price = (h_o[-1] + h_c[-1]) / 2
        
        high_price = max([h[i], close_price, open_price])
        low_price = min([l[i], close_price, open_price])
        
        h_o.append(open_price)
        h_h.append(high_price)
        h_l.append(low_price)
        h_c.append(close_price)

    return h_o, h_h, h_l, h_c

def to_dataframe(o, h, l, c, v):
    df = pd.DataFrame()
    
    df['open'] = o
    df['high'] = h
    df['low'] = l
    df['close'] = c
    df['volume'] = v
    
    return df
    
def ema(s, n):
    s = np.array(s)
    out = []
    j = 1

    #get n sma first and calculate the next n period ema
    sma = sum(s[:n]) / n
    multiplier = 2 / float(1 + n)
    out.append(sma)

    #EMA(current) = ( (Price(current) - EMA(prev) ) x Multiplier) + EMA(prev)
    out.append(( (s[n] - sma) * multiplier) + sma)

    #now calculate the rest of the values
    for i in s[n+1:]:
        tmp = ( (i - out[j]) * multiplier) + out[j]
        j = j + 1
        out.append(tmp)

    return np.array(out)

#def talon_strategy_one():
    # slow = 8
    # fast = 5 
    # ema_0 = ema(h_c, 13)
    
    # vh1 = (np.array(h_l) + np.array(h_c)) / 2
    # vh1 = pd.Series(vh1).rolling(fast).max().dropna().tolist()
    # vh1 = ema(vh1, fast)
    
    # vl1 = (np.array(h_h) + np.array(h_c)) / 2
    # vl1 = pd.Series(vl1).rolling(slow).max().dropna().tolist()
    # vl1 = ema(vl1, slow)
    
    
    # e_ema1 = ema(h_c, 1)
    # e_ema2 = ema(e_ema1, 1)
    # e_ema3 = ema(e_ema2, 1)
    
    # tema = 1 * (e_ema1 - e_ema2) + e_ema3
    
    # e_e1 = ema(h_c, 8)
    # e_e2 = ema(e_e1, 5)
    
    
    # dema = 2 * e_e1 - e_e2

def avarage_true_range(high, low, close):
    
    atr = []
    
    for i, v in enumerate(high):
        if i!= 0:
            value = np.max([high[i] - low[i], np.abs(high[i] - close[i-1]), np.abs(low[i] - close[i-1])])
            atr.append(value)
    return np.array(atr)

def trading_signal(h_o, h_h, h_l, h_c, use_last=False):
    factor = 1
    pd = 1
    
    hl2 = (np.array(h_h) + np.array(h_l)) / 2
    hl2 = hl2[1:]
    
    atr = avarage_true_range(h_h, h_l, h_c)
    
    up = hl2 - (factor * atr)
    dn = hl2 + (factor * atr)
    
    trend_up = [0]
    trend_down = [0]
    
    for i, v in enumerate(h_c[1:]):
        if i != 0:
            
            if h_c[i-1] > trend_up[i-1]:
                trend_up.append(np.max([up[i], trend_up[i-1]]))
            else:
                trend_up.append(up[i])
                
            if h_c[i-1] < trend_down[i-1]:
                trend_down.append(np.min([dn[i], trend_down[i-1]]))
            else:
                trend_down.append(dn[i])
        
    
    trend = []
    last = 0
    for i, v in enumerate(h_c):
        if i != 0:
            if h_c[i] > trend_down[i-1]:
                tr = 1
                last = tr
            elif h_c[i] < trend_up[i-1]:
                tr = -1
                last = tr
            else:
                tr = last
            trend.append(tr)
        
    entry = [0]
    last = 0
    for i, v in enumerate(trend):
        if i != 0:
            if trend[i] == 1 and trend[i-1] == -1:
                entry.append(1)
                last = 1
            
            elif trend[i] == -1 and trend[i-1] == 1:
                entry.append(-1)
                last = -1
            
            else:
                if use_last:
                    entry.append(last)
                else:
                    entry.append(0)
    
    return entry

def get_signal(client, _market="BTCUSDT", _period="15m", use_last=False):
    candles = client.get_candlestick_data(_market, interval=_period)
    o, h, l, c, v = convert_candles(candles)
    h_o, h_h, h_l, h_c = construct_heikin_ashi(o, h, l, c)
    ohlcv = to_dataframe(h_o, h_h, h_l, h_c, v)
    entry = trading_signal(h_o, h_h, h_l, h_c, use_last)
    return entry
    
#%%
#market = "BNBUSDT"
#leverage = 1
#margin_type = "CROSS"
#usdt = get_futures_balance(client, _asset = "USDT")
#initialise_futures(client, _market=market)

#qty = calculate_position_size(client, usdt_balance=usdt, _market=market)
#precision = get_market_precision(client, _market=market)

#qty = round_to_precision(qty, precision)

#execute_order(client, _qty=qty, _side="BUY" , _market=market)

#close_position(client, _market="BNBUSDT")
entry = get_signal(client, _market="BNBUSDT", _period="5m")

exit_trigger = get_liquidation(client, _market="BNBUSDT")
entry_price = get_entry(client, _market="BNBUSDT")

market_price = get_market_price(client, _market="BNBUSDT")

sell_price_trigger = exit_trigger
in_position = True

side = 0 

if entry[-2] == -1:
    print("SELL")
    side = -1
elif entry[-2] == 1:
    print("BUY")
    side = 1
    
plt.plot(entry)
#plt.plot(trend_up)
#plt.plot(trend_down)
#plt.plot(h_c)