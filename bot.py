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

#global values used by bot to keep track of state
entry_price = 0
exit_price_trigger = 0
liquidation_price = 0
in_position = False
side = 0

#Initialise the market leverage and margin type.
bf.initialise_futures(client, _market=market, _leverage=leverage)

while True:
    
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
            side = -1
            in_position = True
            
        #if the second last signal in the generated set of data is 1, then open a LONG
        elif entry[-2] == 1:
            print("BUY")
            bf.initialise_futures(client, _market=market, _leverage=leverage)
            qty = bf.calculate_position(client, market, _leverage=leverage)
            bf.execute_order(client, _qty=qty, _side="BUY" , _market=market)
            side = 1
            in_position = True
    
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
            in_position = False
            side = 0
            exit_price_trigger = 0
        
        #grab our entry price for our position
        if entry_price == 0:
            entry_price = bf.get_entry(client, _market=market)
        
        #set exit trigger that are 2% away from our entry - depending on which side we are. 
        if exit_price_trigger == 0:
            liquidation_price = bf.get_liquidation(client, _market=market)
            exit_price_trigger = liquidation_price
            
            if side == -1:
                exit_price_trigger = entry_price * 1.02
            elif side == 1:
                exit_price_trigger = entry_price * 0.98
                
        # If we are short then consider triggering an exit in this block
        if side == -1:
            
            #if the market has moved 2% in favour of our position, set a new exit trigger
            #this trigger will try to retain half of our gains!
            if market_price < entry_price * 0.98:
                new_exit_price_trigger = (market_price*0.5) + (entry_price * 0.5)
                if new_exit_price_trigger < exit_price_trigger:
                    exit_price_trigger = new_exit_price_trigger
            
            #if the price goes above our exit trigger, then exit the trade
            if market_price > exit_price_trigger:
                bf.close_position(client, _market=market)
                in_position = False
                side = 0
                exit_price_trigger = 0
                liquidation_price = 0
        
        # If we are LONG then consider triggering an exit in this block
        if side == 1:
            
            #if the market has moved 2% in favour of our position, set a new exit trigger
            #this trigger will try to retain half of our gains!
            if market_price > entry_price * 1.02:
                new_exit_price_trigger = (market_price*0.5) + (entry_price*0.5)
                if new_exit_price_trigger > exit_price_trigger:
                   exit_price_trigger = new_exit_price_trigger
                   
            #if the price goes below our exit trigger, then exit the trade
            if market_price < exit_price_trigger:
                bf.close_position(client, _market=market)
                in_position = False
                side = 0
                exit_price_trigger = 0
                liquidation_price = 0
        
        
    #Sleep for a few seconds - Save bandwidth, compute and prevent rate limiting
    time.sleep(6)
    