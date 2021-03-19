from binance.client import Client


client = Client(api_key, api_secret)

# get market depth
#depth = client.get_order_book(symbol='BNBBTC')

# place a test market buy order, to place an actual order use the create_order function
#order = client.create_test_order(
#    symbol='BNBBTC',
#    side=Client.SIDE_BUY,
#    type=Client.ORDER_TYPE_MARKET,
#    quantity=100)

# get all symbol prices
#prices = client.get_all_tickers()


# start aggregated trade websocket for BNBBTC
#def process_message(msg):
#    print("message type: {}".format(msg['e']))
#    print(msg)
    # do something

#from binance.websockets import BinanceSocketManager
#bm = BinanceSocketManager(client)
#bm.start_aggtrade_socket('BNBBTC', process_message)
#bm.start()

# get historical kline data from any date range

# fetch 1 minute klines for the last day up until now
#klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")

# fetch 30 minute klines for the last month of 2017
#klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_30MINUTE, "1 Dec, 2017", "1 Jan, 2018")

# fetch weekly klines since it listed
#klines = client.get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")

def get_futures_balance(client, _asset = "USDT"):
    balances = client.futures_account_balance()
    asset_balance = 0
    for balance in balances:
        if balance['asset'] == _asset:
            asset_balance = balance['balance']
            break
    
    return asset_balance

def initialise_futures(client, _market="BTCUSDT", _leverage=1, _margin_type="CROSS"):
    client.futures_change_leverage(_market, _leverage, _margin_type)

#%%

market = "BTCUSDT"
leverage = 1
margin_type = "CROSS"
usdt = get_futures_balance(client, asset = "USDT")


