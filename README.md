# Binance Futures Bot

A simple bot that trades futures on binance.

## Supporting this project
If you'd like to support my work please consider: 

* [donating to the patreon](https://www.patreon.com/SingularitAI)
* [Supporting on github](https://github.com/sponsors/hephyrius)
* [Following the youtube channel](https://www.youtube.com/channel/UCamWRprZmZ02TJAvGCCZzYg)

## Table of Contents  
* [Disclaimer](#Disclaimer)  
* [Trading Strategy](#Trading-Strategy)  
* [Bot Specifics](#Bot-Specifics)  
* [Installation](#Installation)  
* [Setup](#Setup)  
* [Useage](#Useage)  
* [Misc](#Misc)  

## Disclaimer

### This bot is intended to be a Proof-of-concept. The developer will not be responsible for any losses that are a result of using this program. This program or anything related to it, should not be considered investment advice. Understand the risks involved, do your own research and only trade with amounts you are willing to lose. 

## Trading Strategy

The bot trades a strategy called the ['TalonSniper'](https://www.tradingview.com/script/Kt8v4HcD-Talon-Sniper-v1/). It can be modified to take your own stragies.

![image of strategy](https://github.com/Hephyrius/binance_futures_bot/blob/main/images/talon_chart.png)

### Why this strategy?

I chose the strategy as a demonstration strategy. I came across it while browsing trading view. On the surface the strategy seems to find points where trends can be considered "confirmed". The strategy was reimplemented by looking at the code in the trading view pine editor and then recreating it in python. This can be found in the trading_signal() function of the bot_functions.py file.

### Heikin Ashi Candles

The Bot makes use of Heikin Ashi candles for it's candle representations. This is because Heikin Ashi candles make it easier to spot trends. You can read more about them [here](https://www.investopedia.com/terms/h/heikinashi.asp)

## Bot Specifics

### Position Entry

Positions are given to a bot as a list of historic "signals". These tell the bot when to go long, short or stay in whatever it was in before.

* Long is represented by 1
* Short is represented by -1
* Stay/do nothing is represented by 0

The bot uses the second last signal from the list of historic signals to make it's choice of action. This is because the last signal in the list is the current unresolved candle, as this is still in flux. 

### Position Exit
The bot attempts to stay in positions as long as possible.

* If the bot is in a position and the signal changes to counter of the current position, the bot will close position and open a new on on the opposite side
* When the bot enters a position it submits a trailing stop market that is a certain % away from entry. This will prevent big losses in case of bot failure and lock in bigger profits - depending on % used.

### Changing Strategies

If you want to swap out the falcon sniper strategy with one of your own, I recommend doing it like so.

First Create a function that calculates some sort of signal and returns it as a list of integers. Taking Heikin Ashi open, high, low, and close as inputs.

``` python
def new_trading_signal(h_o, h_h, h_l, h_c, use_last=False):

    entry = [0]
    last = 0
    for i, v in enumerate(h_o):
        if i != 0:
            if h_o[i-1] < h_c[i-1]:
                entry.append(1)
                last = 1
            
            elif h_o[i-1] > h_c[i-1]:
                entry.append(-1)
                last = -1
            
            else:
                if use_last:
                    entry.append(last)
                else:
                    entry.append(0)
    
    return entry
```

Then modify the function the bot calls for its entry signalling.

``` python
def get_signal(client, _market="BTCUSDT", _period="15m", use_last=False):
    candles = client.get_candlestick_data(_market, interval=_period)
    o, h, l, c, v = convert_candles(candles)
    h_o, h_h, h_l, h_c = construct_heikin_ashi(o, h, l, c)
    ohlcv = to_dataframe(h_o, h_h, h_l, h_c, v)
    entry = new_trading_signal(h_o, h_h, h_l, h_c, use_last)
    return entry
```

NOTE: the use_last variable allows you to constantly pump out the last non-zero bot signal. This will allow the bot to enter a position as soon as the bot is initiated, rather than it waiting for a new signal to appear. This can also be chained with multi-timescale strategies for better potential performance.

## Installation

### Requirements

The bot doesn't require much to operate. Simple Numpy, Pandas and [binance futures python](https://github.com/Binance-docs/Binance_Futures_python)

you can install some of the requirements as such:

```
pip install -r requirements.txt
```

followed by the installation of [binance futures python](https://github.com/Binance-docs/Binance_Futures_python)

```
python -m pip install git+https://github.com/Binance-docs/Binance_Futures_python.git

```

## Setup

The bot can be modified for use with any USDT futures market, leverage and time frame combinatiob by editing the settings.json file. 

### Settings.json

You should replace the market, leverage and period with values that are relevant.

* Market - this is the binance usdt futures market you would like to trade. it is usually the ticker of the coin followed by usdt. For insance ethereum would be "ETHUSDT" and tron would be "TRXUSDT". You can usually find the market name on binance.
* Period value - this represents the timescales at which the strategy will trade signals. represented as minutes, hours or days. Valid : 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d. To use aggregate signals across multiple time scales, you should seperate the values with a comma. 
* Leverage - This is the leverage amount you would like to apply to your trades. The Leverage on binance can go up to 125x, however the maximum leverage is dependant on market.
* Margin_type - this is if youd like to use ISOLATED margin and protect your account value or CROSSED and use the entire account value as margin for the trades.
* trailing_percentage - percentage the trailing stop should follow. This will act as a fail safe incase the bot fails or enters a bad trade, and will help lock in profits on the good trades.
```
{
	"market": "BTCUSDT",
	"leverage": "5",
	"period": "5m,15m",
	"margin_type": "CROSSED",
	"trailing_percentage": "2.0"
}
```

### Keys.json

This file is where you should put your API keys. The API Keys should have Futures access enabled, or the bot won't work. [You can generate a new api key here when logged in to binance](https://www.binance.com/en/my/settings/api-management)

```
{
	"api_key": "fill_api_key_here",
	"api_secret": "fill_api_secret_here"
}
```


## Useage

Once you've modified Keys.json and Settings.json you should be ready to go.

### Running locally

```
python bot.py
```

### Running on a linux server/cloud insance

```
nohup python bot.py &
```

## Misc

### Does this make $$$?

tl;dr - Short answer yes and no!

This really depends on market conditions, leverage and time period! The bot seems to struggle when the market is side-ways, but seems to excell when trending. But again this depends on settings and specific markets. Nothing is guaranteed ( refer to [Disclaimer](#Disclaimer) ). 

### Liquidation Price

The bot does not take into account liquidation price, although a function has been created for this purpose. Be careful when using any leverage where a 2% move can lead to liquidation of positions - I advice against using leverage sizes that are crazy high (i.e. 30x+)
