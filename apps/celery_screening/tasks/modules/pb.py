import asyncio
import ccxt.async_support as ccxt

exchange =  ccxt.binance({
    'apiKey': '9WxB9E2ZQybl0dSyZnYT6ja6NO4vQ0eNqdSU9tYsu9x877iTa1anhEVWd8a6t4fC',
    'secret': 'DkjrKTIPyk57pXmNuC5G2aNxppHVEQXKQ8wC8hbk1xh0ysB90NVxODHoV6f9BLEQ',
    'enableRateLimit': True,
    })

async def fetch_balance():

    try:
        balance = await exchange.fetch_balance()
        print(balance)
        ticker = await exchange.fetch_ticker('BTC/USDT')
        print(ticker)
    finally:
        await exchange.close()
asyncio.run(fetch_balance())



# async def fetch_ticker():
#     binance = ccxt.binance()
#     ticker = await binance.fetch_ticker('BTC/USDT')
#     print(f"Курс BTC/USDT: {ticker['last']}")
#     await binance.close()
#
# asyncio.run(fetch_ticker())
