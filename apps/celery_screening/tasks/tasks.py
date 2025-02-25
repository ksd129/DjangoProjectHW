import asyncio
import logging
import urllib

import aiohttp
import requests
from celery import shared_task

from apps.celery_screening.logs.log_config import logger, file_handler, formatter
from apps.celery_screening.models import Ticker24hrUSDT, Candles1mUSDT, SymbolList, AllCandlesUSDT
from core.settings import env
from django.db import transaction, IntegrityError

from asgiref.sync import async_to_sync, sync_to_async



# Создайте логгер
logger.setLevel(logging.DEBUG)

# Создайте обработчик для записи логов в файл
file_handler.setLevel(logging.DEBUG)

# Создайте форматтер и добавьте его к обработчику
file_handler.setFormatter(formatter)

# Добавьте обработчик к логгеру
logger.addHandler(file_handler)



class BinanceAPIUrl:
    BASE_URL = f"{env.str('URL_BINANCE')}{env.str('TICKER_KLINES')}"

    @staticmethod
    def generate_klines_url(symbol, interval, start_time, end_time, limit):
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        url = f"{BinanceAPIUrl.BASE_URL}?{urllib.parse.urlencode(params)}"
        return url


class TradingIndicators:

    @staticmethod
    def calculate_atr(high, low, open_price):
        atr = max(high - low, abs(high - open_price), abs(low - open_price))
        return atr

#Типичная цена
    @staticmethod
    def calculate_tp(high, low, close):
        tp = (high + low + close) / 3
        return tp



@shared_task
def get_ticker_all_pairs_usdt():
    url = f"{env.str('URL_BINANCE')}{env.str('TICKER_24HR')}"
    response = requests.get(url)
    data = response.json()
    usdt_pairs = [pair for pair in data if pair['symbol'].endswith('USDT') and float(pair.get('weightedAvgPrice', 0)) != 0]


    SymbolList.objects.update_or_create(
        id=1,
        defaults={
            'symbols': ','.join([item['symbol'] for item in usdt_pairs]),  # Сохраните символы как строку, разделённую запятыми
        }
    )

    with transaction.atomic():
        for item in usdt_pairs:
            Ticker24hrUSDT.objects.update_or_create(
                symbol=item['symbol'],
                defaults={
                    'price_change': float(item['priceChange']),
                    'price_change_percent': float(item['priceChangePercent']),
                    'weighted_avg_price': float(item['weightedAvgPrice']),
                    'prev_close_price': float(item['prevClosePrice']),
                    'last_price': float(item['lastPrice']),
                    'last_qty': float(item['lastQty']),
                    'bid_price': float(item['bidPrice']),
                    'bid_qty': float(item['bidQty']),
                    'ask_price': float(item['askPrice']),
                    'ask_qty': float(item['askQty']),
                    'open_price': float(item['openPrice']),
                    'high_price': float(item['highPrice']),
                    'low_price': float(item['lowPrice']),
                    'volume': float(item['volume']),
                    'quote_volume': float(item['quoteVolume']),
                    'open_time': int(item['openTime']),
                    'close_time': int(item['closeTime']),
                    'first_id': int(item['firstId']),
                    'last_id': int(item['lastId']),
                    'count': int(item['count']),
                }
            )



@shared_task
def get_ticker_all_pairs_usdt_candles_1m():
    symbol_list = SymbolList.objects.get(id=1)
    coins = symbol_list.symbols.split(',')

    async def fetch_data(session, url, coin):
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for candles in data:
                    try:
                        Candles1mUSDT.objects.update_or_create(
                            symbol=coin,
                            defaults={
                                'open_time': int(candles[0]),
                                'open_price': float(candles[1]),
                                'high_price': float(candles[2]),
                                'low_price': float(candles[3]),
                                'close_price': float(candles[4]),
                                'volume': float(candles[5]),
                                'close_time': int(candles[6]),
                                'base_asset_volume': float(candles[7]),
                                'count': int(candles[8]),
                                'taker_buy_volume': float(candles[9]),
                                'taker_buy_base_asset_volume': float(candles[10]),
                            }
                        )
                    except IntegrityError:
                        print(f"Error updating/creating data for {coin}")
            else:
                print(f"Error fetching data for {coin}")

    async def main():
        async with aiohttp.ClientSession() as session:
            tasks = []
            for coin in coins:
                url = BinanceAPIUrl.generate_klines_url(symbol=coin)
                tasks.append(fetch_data(session, url, coin))
            await asyncio.gather(*tasks)

    asyncio.run(main())


# Асинхронное выполнение запросов
@shared_task
def get_ticker_all_pairs_usdt_candles_by_parameters(start_time=None, end_time=None, field_db='all_candles_1mo_in_1y', interval='1M', limit=12):
    async def fetch_data(session, url, coin):
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f"API request failed for {coin} with status code: {response.status}")
                return None
            data = await response.json()
            return coin, data

    async def main():
        logger.info(f"Starting task: get_ticker_all_pairs_usdt_{field_db}")
        try:
            symbol_list = await sync_to_async(SymbolList.objects.get)(id=1)
            coins = symbol_list.symbols.split(',')

            async with aiohttp.ClientSession() as session:
                tasks = []
                for coin in coins:
                    url = BinanceAPIUrl.generate_klines_url(start_time=start_time, end_time=end_time, symbol=coin, interval=interval, limit=limit)
                    tasks.append(fetch_data(session, url, coin))

                responses = await asyncio.gather(*tasks)
                for result in responses:
                    if result:
                        coin, data = result
                        candles_list = [{
                            'open_time': int(candles[0]),
                            'open_price': float(candles[1]),
                            'high_price': float(candles[2]),
                            'low_price': float(candles[3]),
                            'close_price': float(candles[4]),
                            'volume': float(candles[5]),
                            'close_time': int(candles[6]),
                            'base_asset_volume': float(candles[7]),
                            'count': int(candles[8]),
                            'taker_buy_volume': float(candles[9]),
                            'taker_buy_base_asset_volume': float(candles[10]),
                            'indicators': {
                                'ATR': float(TradingIndicators.calculate_atr(
                                    high=float(candles[2]),
                                    low=float(candles[3]),
                                    open_price=float(candles[1])
                                )),
                                'TP': float(TradingIndicators.calculate_tp(
                                    high=float(candles[2]),
                                    low=float(candles[3]),
                                    close=float(candles[4])
                                )),
                            }
                        } for candles in data]

                        await sync_to_async(AllCandlesUSDT.objects.update_or_create)(
                            symbol=coin,
                            defaults={field_db: candles_list}
                        )

            logger.info(f"Completed task: get_ticker_all_pairs_usdt_{field_db}")

        except Exception as e:
            logger.error(f"An error occurred: {e}")

    async_to_sync(main)()


def



# запуск задач после запуска Celery
# @worker_ready.connect
# def at_startup(sender, **kwargs):
#     start_time = None
#     end_time = None
#     field_db = 'all_candles_5m_in_24hr'
#     interval = '5m'
#     limit = 288
#
#     # Запустите задачу с параметрами
#     get_ticker_all_pairs_usdt_candles_by_parameters.apply_async(args=(start_time, end_time, field_db, interval, limit))






