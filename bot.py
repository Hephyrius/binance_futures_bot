import json
import time
import bot_functions as bf

#Load our credentials from json, instead of hard coding.
api_info = json.load(open ("keys.json", "r"))
api_key = api_info['api_key']
api_secret = api_info['api_secret']

#Connect to the binance api and produce a client
client = bf.init_client(api_key, api_secret)

#Load settings from settings.json
bot_settings = json.load(open ("settings.json", "r"))
market = bot_settings['market']
leverage = int(bot_settings['leverage'])
margin_type = bot_settings['margin_type']
period = bot_settings['period']
trailing_percentage = float(bot_settings['trailing_percentage'])

#global values used by bot to keep track of state
entry_price = 0
side = 0
in_position = False

#Initialise the market leverage and margin type.
bf.initialise_futures(client, _market=market, _leverage=leverage)

while True:
    try:
        #if not currently in a position then execute this set of logic
        if in_position == False:
            
            #generate signal data for the last 500 candles
            entry = bf.get_signal(client, _market=market, _period=period)
            
            #if the second last signal in the generated set of data is -1, then open a SHORT
            if entry[-2] == -1:
                print("SELL")
                bf.initialise_futures(client, _market=market, _leverage=leverage)
                qty = bf.calculate_position(client, market, _leverage=leverage)
                bf.execute_order(client, _qty=qty, _side="SELL" , _market=market)
                market_price = bf.get_market_price(client, _market=market)
                side = -1
                in_position = True
                
                #close any open trailing stops we have
                client.cancel_all_orders(market)
                time.sleep(3)
    
                bf.log_trade(_qty=qty, _market=market, _leverage=leverage, _side=side,
                  _cause="Signal Change", _trigger_price=0, 
                  _market_price=market_price, _type="Enter")
                
                #Let the order execute and then create a trailing stop market order.
                time.sleep(3)
                bf.submit_trailing_order(client, _market=market, _qty =qty, _side="BUY",
                                         _callbackRate=trailing_percentage)
                
            #if the second last signal in the generated set of data is 1, then open a LONG
            elif entry[-2] == 1:
                print("BUY")
                bf.initialise_futures(client, _market=market, _leverage=leverage)
                qty = bf.calculate_position(client, market, _leverage=leverage)
                bf.execute_order(client, _qty=qty, _side="BUY" , _market=market)
                market_price = bf.get_market_price(client, _market=market)
                side = 1
                in_position = True
                
                #close any open trailing stops we have
                client.cancel_all_orders(market)
                time.sleep(3)
                
                bf.log_trade(_qty=qty, _market=market, _leverage=leverage, _side=side,
                  _cause="Signal Change", _trigger_price=0, 
                  _market_price=market_price, _type="Enter")
                
                #Let the order execute and then create a trailing stop market order.
                time.sleep(3)
                bf.submit_trailing_order(client, _market=market, _qty =qty, _side="SELL",
                                         _callbackRate=trailing_percentage)
        
        #If already in a position then check market and decide when to exit
        elif in_position == True:
            
            #generate signal data for the last 500 candles
            entry = bf.get_signal(client, _market=market, _period=period)
            
            #get the last market price
            market_price = bf.get_market_price(client, _market=market)
            
            #if we generated a signal that is the opposite side of what our position currently is
            #then sell our position. The bot will open a new position on the opposite side when it loops back around!
            if entry[-2] != side and entry[-2] != 0:
                bf.close_position(client, _market=market)
                
                #close any open trailing stops we have
                client.cancel_all_orders(market)
                time.sleep(1)
                
                bf.log_trade(_qty=qty, _market=market, _leverage=leverage, _side=side,
                              _cause="Signal Change", _market_price=market_price, 
                              _type="EXIT")
                
                in_position = False
                side = 0
                
                
            position_active = bf.check_in_position(client, market)
            if position_active == False:
                bf.log_trade(_qty=qty, _market=market, _leverage=leverage, _side=side,
                  _cause="Signal Change", _market_price=market_price, 
                  _type="Trailing Stop")
                in_position = False
                side = 0
                
                #close any open trailing stops we have one
                client.cancel_all_orders(market)
                time.sleep(1)
            
        time.sleep(6)
    except Exception as e:
        print(f"Encountered Exception {e}")
        time.sleep(10)

