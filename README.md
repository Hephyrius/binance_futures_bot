# binance_futures_bot

A simple bot that trades futures on binance. 

##### Table of Contents  
[Disclaimer](#Disclaimer)  
[Trading Strategy](#Trading-Strategy)
[Setup](#Setup)  
[Useage](#Useage)  
[Modification](#Modification)  

## Disclaimer

### This bot is intended to be a Proof-of-concept. The developer will not be responsible for any losses that are a result of using this program. This program or anything related to it, should not be considered investment advice. Understand the risks involved, do your own research and only trade with amounts you are willing to lose. 

## Trading Strategy

The bot trades a strategy called the ['TalonSniper'](https://www.tradingview.com/script/Kt8v4HcD-Talon-Sniper-v1/). It can be modified to take your own stragies.

![image of strategy](https://github.com/Hephyrius/binance_futures_bot/blob/main/images/talon_chart.png)

### Why this strategy?

I came across this strategy while browsing trading view. On the surface the strategy seems to find points where trends can be considered "confirmed". The strategy was reimplemented by looking at the code in the trading view pine editor and then recreating it in python. This can be found in the trading_signal() function of the bot_functions.py file.

# Modification

The bot can be modified for use with any USDT futures market, leverage and time frame combinatiob by editing the settings.json file. 