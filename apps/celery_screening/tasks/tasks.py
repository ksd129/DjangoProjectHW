import asyncio
import logging
import urllib

import aiohttp
import requests
from celery import shared_task
from apps.celery_screening.models import Ticker24hrUSDT, Candles1mUSDT, SymbolList, AllCandlesUSDT
from core.settings import env
from django.db import transaction

from asgiref.sync import async_to_sync, sync_to_async

from concurrent.futures import ThreadPoolExecutor, as_completed

from celery.signals import worker_ready

# Создайте логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Создайте обработчик для записи логов в файл
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)

# Создайте форматтер и добавьте его к обработчику
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
def get_ticker_all_pairs_usdt_candles_1m(c_count=25):
    symbol_list = SymbolList.objects.get(id=1)
    coins = symbol_list.symbols  # Получаем строку символов
    coins_list = coins.split(',')
    exit_count = 0

    for coin in coins_list:
        exit_count += 1
        if exit_count == c_count:
            break

        url = BinanceAPIUrl.generate_klines_url(symbol=coin)
        response = requests.get(url)
        data = response.json()

        for candles in data:
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
                            'taker_buy_base_asset_volume': float(candles[10])
                        } for candles in data]

                        await sync_to_async(AllCandlesUSDT.objects.update_or_create)(
                            symbol=coin,
                            defaults={field_db: candles_list}
                        )

            logger.info(f"Completed task: get_ticker_all_pairs_usdt_{field_db}")

        except Exception as e:
            logger.error(f"An error occurred: {e}")

    async_to_sync(main)()




# Параллельное выполнение запросов
# @shared_task
# def get_ticker_all_pairs_usdt_candles_by_parameters(start_time=None, end_time=None, field_db='all_candles_1mo_in_1y', interval='1M', limit=12):
#     logger.info(f"Starting task: get_ticker_all_pairs_usdt_{field_db}")
#
#     def fetch_data(url, coin):
#         response = requests.get(url)
#         if response.status_code != 200:
#             logger.error(f"API request failed for {coin} with status code: {response.status_code}")
#             return None
#         data = response.json()
#         return coin, data
#
#     try:
#         symbol_list = SymbolList.objects.get(id=1)
#         coins = symbol_list.symbols.split(',')
#
#         with ThreadPoolExecutor(max_workers=10) as executor:
#             futures = []
#             for coin in coins:
#                 url = BinanceAPIUrl.generate_klines_url(start_time=start_time, end_time=end_time, symbol=coin, interval=interval, limit=limit)
#                 futures.append(executor.submit(fetch_data, url, coin))
#
#             for future in as_completed(futures):
#                 result = future.result()
#                 if result:
#                     coin, data = result
#                     candles_list = [{
#                         'open_time': int(candles[0]),
#                         'open_price': float(candles[1]),
#                         'high_price': float(candles[2]),
#                         'low_price': float(candles[3]),
#                         'close_price': float(candles[4]),
#                         'volume': float(candles[5]),
#                         'close_time': int(candles[6]),
#                         'base_asset_volume': float(candles[7]),
#                         'count': int(candles[8]),
#                         'taker_buy_volume': float(candles[9]),
#                         'taker_buy_base_asset_volume': float(candles[10])
#                     } for candles in data]
#
#                     obj, created = AllCandlesUSDT.objects.update_or_create(
#                         symbol=coin,
#                         defaults={field_db: candles_list}
#                     )
#
#                     if created:
#                         logger.info(f"Created new record for {coin}")
#                     else:
#                         logger.info(f"Updated record for {coin}")
#
#         logger.info(f"Completed task: get_ticker_all_pairs_usdt_{field_db}")
#
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")



# Последовательное выполнение запросов
# @shared_task
# def get_ticker_all_pairs_usdt_candles_by_parameters(start_time=None, end_time=None, field_db='all_candles_1mo_in_1y', interval='1M', limit=12):
#     logger.info(f"Starting task: get_ticker_all_pairs_usdt_{field_db}")
#
#     try:
#         symbol_list = SymbolList.objects.get(id=1)
#         coins = symbol_list.symbols  # Получаем строку символов
#         coins_list = coins.split(',')
#
#         for coin in coins_list:
#             url = BinanceAPIUrl.generate_klines_url(start_time=start_time, end_time=end_time, symbol=coin, interval=interval, limit=limit)
#             response = requests.get(url)
#
#             if response.status_code != 200:
#                 logger.error(f"API request failed for {coin} with status code: {response.status_code}")
#                 continue
#
#             data = response.json()
#
#             candles_list = [{
#                 'open_time': int(candles[0]),
#                 'open_price': float(candles[1]),
#                 'high_price': float(candles[2]),
#                 'low_price': float(candles[3]),
#                 'close_price': float(candles[4]),
#                 'volume': float(candles[5]),
#                 'close_time': int(candles[6]),
#                 'base_asset_volume': float(candles[7]),
#                 'count': int(candles[8]),
#                 'taker_buy_volume': float(candles[9]),
#                 'taker_buy_base_asset_volume': float(candles[10])
#             } for candles in data]
#
#             obj, created = AllCandlesUSDT.objects.update_or_create(
#                 symbol=coin,
#                 defaults={
#                     field_db: candles_list,
#                 }
#             )
#
#             if created:
#                 logger.info(f"Created new record for {coin}")
#             else:
#                 logger.info(f"Updated record for {coin}")
#
#         logger.info("Completed task: get_ticker_all_pairs_usdt_candles_1mo_in_1year")
#
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")





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






