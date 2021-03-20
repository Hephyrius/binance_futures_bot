import json
import time
import bot_functions as bf

#Load our credentials from json, instead of hard coding.
api_info = json.load(open ("keys.json", "r"))
api_key = api_info['api_key']
api_secret = api_info['api_secret']

#Connect to the binance api
client = bf.init_client(api_key, api_secret)

market = "LTCUSDT"
leverage = 5
margin_type = "CROSSED"
period = "5m"

bf.initialise_futures(client, _market=market, _leverage=leverage)

entry_price = 0
exit_price_trigger = 0
liquidation_price = 0
in_position = False
side = 0

while True:
    if in_position == False:
        entry = bf.get_signal(client, _market=market, _period=period)
        if entry[-2] == -1:
            print("SELL")
            bf.initialise_futures(client, _market=market, _leverage=leverage)
            qty = bf.calculate_position(client, market, _leverage=leverage)
            bf.execute_order(client, _qty=qty, _side="SELL" , _market=market)
            side = -1
            in_position = True
        elif entry[-2] == 1:
            print("BUY")
            bf.initialise_futures(client, _market=market, _leverage=leverage)
            qty = bf.calculate_position(client, market, _leverage=leverage)
            bf.execute_order(client, _qty=qty, _side="BUY" , _market=market)
            side = 1
            in_position = True
            
    elif in_position == True:
        entry = bf.get_signal(client, _market=market, _period=period)
        market_price = bf.get_market_price(client, _market=market)
        
        if entry[-2] != side and entry[-2] != 0:
            bf.close_position(client, _market=market)
            in_position = False
            side = 0
            exit_price_trigger = 0
        
        if entry_price == 0:
            entry_price = bf.get_entry(client, _market=market)
         
        if exit_price_trigger == 0:
            liquidation_price = bf.get_liquidation(client, _market=market)
            exit_price_trigger = liquidation_price
            
            if side == -1:
                exit_price_trigger = entry_price * 1.02
            elif side == 1:
                exit_price_trigger = entry_price * 0.98
                
        
        if side == -1:
            
            if market_price < entry_price * 0.98:
                new_exit_price_trigger = (market_price*0.5) + (entry_price * 0.5)
                if new_exit_price_trigger < exit_price_trigger:
                    exit_price_trigger = new_exit_price_trigger
            
            if market_price > exit_price_trigger:
                bf.close_position(client, _market=market)
                in_position = False
                side = 0
                exit_price_trigger = 0
                liquidation_price = 0
            
        if side == 1:
            
            if market_price > entry_price * 1.02:
                new_exit_price_trigger = (market_price*0.5) + (entry_price*0.5)
                if new_exit_price_trigger > exit_price_trigger:
                   exit_price_trigger = new_exit_price_trigger
            
            if market_price < exit_price_trigger:
                bf.close_position(client, _market=market)
                in_position = False
                side = 0
                exit_price_trigger = 0
                liquidation_price = 0
        
        
    time.sleep(10)
    