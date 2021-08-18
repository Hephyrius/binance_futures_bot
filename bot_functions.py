from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
import pandas as pd
import numpy as np
import time
import sys, os
import config as cfg

def getStdOut():
    return sys.stdout

def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint(std):
    sys.stdout = std

def singlePrint(string, std):
    enablePrint(std)
    print(string)
    blockPrint()

#create a binance request client
def init_client():
    client = RequestClient(api_key=cfg.getPublicKey(), secret_key=cfg.getPrivateKey(), url=cfg.getBotSettings().api_url)
    return client

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
    except Exception as e:
        print(e)

    try:
        client.change_margin_type(_market, _margin_type)
    except Exception as e:
        print(e)

#get all of our open orders in a market
def get_orders(client, _market="BTCUSDT"):
    orders = client.get_open_orders(_market)
    return orders, len(orders)

#get all of our open trades
def get_positions(client):
    positions = client.get_position_v2()
    return positions

#get trades we opened in the market the bot is trading in
def get_specific_positon(client, _market="BTCUSDT"):
    positions = get_positions(client)

    for position in positions:
        if position.symbol == _market:
            break

    return position

#close opened position
def close_position(client, _market="BTCUSDT"):
    position = get_specific_positon(client, _market)
    qty = float(position.positionAmt)

    _side = "BUY"
    if qty > 0.0:
        _side = "SELL"

    if qty < 0.0:
        qty = qty * -1

    qty = str(qty)

    execute_order(client, _market=_market,
                  _qty = qty,
                  _side = _side)

#get the liquidation price of the position we are in. - We don't use this - be careful!
def get_liquidation(client, _market="BTCUSDT"):
    position = get_specific_positon(client, _market)
    price = position.liquidationPrice
    return price

#Get the entry price of the position the bot is in
def get_entry(client, _market="BTCUSDT"):
    position = get_specific_positon(client, _market)
    price = position.entryPrice
    return price

#Execute an order, this can open and close a trade
def execute_order(client, _market="BTCUSDT", _type = "MARKET", _side="BUY", _position_side="BOTH", _qty = 1.0):
    client.post_order(symbol=_market,
                      ordertype=_type,
                      side=_side,
                      positionSide=_position_side,
                      quantity = _qty)

#calculate how big a position we can open with the margin we have and the leverage we are using
def calculate_position_size(client, usdt_balance=1.0, _market="BTCUSDT", _leverage=1):
    price = client.get_symbol_price_ticker(_market)
    price = price[0].price

    qty = (float(usdt_balance) / price) * _leverage
    qty = round(qty * 0.99,8)

    return qty

#check if the position is still active, or if the trailing stop was hit.
def check_in_position(client, _market="BTCUSDT"):
    position = get_specific_positon(client, _market)

    in_position = False

    if float(position.positionAmt) != 0.0:
        in_position = True

    return in_position


#Create a trailing stop to close our order if something goes bad, lock in profits or if the trade goes against us!
def submit_trailing_order(client, _market="BTCUSDT", _type = "TRAILING_STOP_MARKET", _side="BUY",
                          _qty = 1.0, _callbackRate=4):

    client.post_order(symbol=_market,
                      ordertype=_type,
                      side=_side,
                      callbackRate=_callbackRate,
                      quantity = _qty,
                      workingType="CONTRACT_PRICE")


# get the current market price
def get_market_price(client, _market="BTCUSDT"):
    price = client.get_symbol_price_ticker(_market)
    price = price[0].price
    return price

# get the precision of the market, this is needed to avoid errors when creating orders
def get_market_precision(client, _market="BTCUSDT"):

    market_data = client.get_exchange_information()
    precision = 3
    for market in market_data.symbols:
        if market.symbol == _market:
            precision = market.quantityPrecision
            break
    return precision

# round the position size we can open to the precision of the market
def round_to_precision(_qty, _precision):
    new_qty = "{:0.0{}f}".format(_qty , _precision)
    return float(new_qty)

# convert from client candle data into a set of lists
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

#convert list candle data into list of heikin ashi candles
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

def handle_signal(client, std, market="BTCUSDT", leverage=3, order_side="BUY", 
                  stop_side="SELL", _callbackRate=2.0):
    initialise_futures(client, _market=market, _leverage=leverage)
    qty = calculate_position(client, market, _leverage=leverage)

    enablePrint(std)
    execute_order(client, _qty=qty, _side=order_side, _market=market)
    blockPrint()

    market_price = get_market_price(client, _market=market)

    side = -1
    if order_side == "BUY":
        side = 1
    else:
        side = -1
        
    in_position = True

    singlePrint(f"{order_side}: {qty} ${market_price} using x{leverage} leverage", std)

    #close any open trailing stops we have
    client.cancel_all_orders(market)
    time.sleep(3)

    log_trade(_qty=qty, _market=market, _leverage=leverage, _side=side,
      _cause="Signal Change", _trigger_price=0, 
      _market_price=market_price, _type=order_side)

    #Let the order execute and then create a trailing stop market order.
    time.sleep(3)
    submit_trailing_order(client, _market=market, _qty =qty, _side=stop_side,
                             _callbackRate=_callbackRate)

    return qty, side, in_position

#create a dataframe for our candles
def to_dataframe(o, h, l, c, v):
    df = pd.DataFrame()

    df['open'] = o
    df['high'] = h
    df['low'] = l
    df['close'] = c
    df['volume'] = v

    return df

#Exponential moving avg - unused
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

#Avarage true range function used by our trading strat
def avarage_true_range(high, low, close):

    atr = []

    for i, v in enumerate(high):
        if i!= 0:
            value = np.max([high[i] - low[i], np.abs(high[i] - close[i-1]), np.abs(low[i] - close[i-1])])
            atr.append(value)
    return np.array(atr)

#Our trading strategy - it takes in heikin ashi open, high, low and close data and returns a list of signal values
#signals are -1 for short, 1 for long and 0 for do nothing
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

#get the data from the market, create heikin ashi candles and then generate signals
#return the signals to the bot
def get_signal(client, _market="BTCUSDT", _period="15m", use_last=False):
    candles = client.get_candlestick_data(_market, interval=_period)
    o, h, l, c, v = convert_candles(candles)
    h_o, h_h, h_l, h_c = construct_heikin_ashi(o, h, l, c)
    ohlcv = to_dataframe(h_o, h_h, h_l, h_c, v)
    entry = trading_signal(h_o, h_h, h_l, h_c, use_last)
    return entry

#get signal that is confirmed across multiple time scales
def get_multi_scale_signal(client, _market="BTCUSDT", _periods=["1m"]):

    signals = np.zeros(499)
    use_last = True

    for i, v in enumerate(_periods):
  
        _signal = get_signal(client, _market, _period= v, use_last=use_last)
        signals = signals + np.array(_signal)

    signals = signals / len(_periods)

    trade_signal = []

    for i, v in enumerate(list(signals)):

        if v == -1:
            trade_signal.append(-1)
        elif v == 1:
            trade_signal.append(1)
        else:
            trade_signal.append(0)

    return trade_signal

#calculate a rounded position size for the bot, based on current USDT holding, leverage and market
def calculate_position(client, _market="BTCUSDT", _leverage=1):
    usdt = get_futures_balance(client, _asset = "USDT")
    qty = calculate_position_size(client, usdt_balance=usdt, _market=_market, _leverage=_leverage)
    precision = get_market_precision(client, _market=_market)
    qty = round_to_precision(qty, precision)
    return qty

#function for logging trades to csv for later analysis
def log_trade(_qty=0, _market="BTCUSDT", _leverage=1, _side="long", _cause="signal", _trigger_price=0, _market_price=0, _type="exit"):
    df = pd.read_csv("trade_log.csv")
    df2 = pd.DataFrame()
    df2['time'] = [time.time()]
    df2['market'] = [_market]
    df2['qty'] = [_qty]
    df2['leverage'] = [_leverage]
    df2['cause'] = [_cause]
    df2['side'] = [_side]
    df2['trigger_price'] = [_trigger_price]
    df2['market_price'] = [_market_price]
    df2['type'] = [_type]

    df = df.append(df2, ignore_index=True)
    df.to_csv("trade_log.csv", index=False)
