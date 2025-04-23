
import asyncio

import aiohttp
import requests
import logging
import aioredis
from celery import shared_task
from apps.celery_screening.models import Ticker24hrUSDT, Candles1mUSDT, SymbolList, AllCandlesUSDT
from apps.celery_screening.tasks.modules.binance_client import BinanceAPIUrl
from core.settings import env
from django.db import transaction, IntegrityError

from asgiref.sync import async_to_sync, sync_to_async


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


async def acquire_semaphore(redis, semaphore_key, limit, timeout=60):
    """Acquire a semaphore using Redis."""
    while True:
        count = await redis.incr(semaphore_key)
        if count <= limit:
            await redis.pexpire(semaphore_key, timeout * 1000)  # Set expiration
            return True
        else:
            await redis.decr(semaphore_key)  # Decrement if limit exceeded
            await asyncio.sleep(1)  # Wait and retry

async def release_semaphore(redis, semaphore_key):
    """Release a semaphore using Redis."""
    await redis.decr(semaphore_key)




@shared_task()
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
@shared_task()
def get_ticker_all_pairs_usdt_candles_by_parameters(start_time=None,
                                                    end_time=None,
                                                    field_db='all_candles_1mo_in_1y',
                                                    interval='1M',
                                                    limit=12):
    # def reset_auto_increment():
    #     # Удалите все записи из таблицы
    #     AllCandlesUSDT.objects.all().delete()
    #
    #     # Сбросьте автоинкрементное значение
    #     with connection.cursor() as cursor:
    #         cursor.execute("ALTER SEQUENCE celery_screening_allcandlesusdt_id_seq RESTART WITH 1;")
    #         # Примечание: замените your_app на имя вашего приложения
    #
    # # Пример использования
    # reset_auto_increment()

    async def fetch_data(session, url, coin, redis):
        if not await acquire_semaphore(redis, "binance_api_semaphore", 1000):
            return None
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"API request failed for {coin} with status code: {response.status}")
                    return None
                data = await response.json()
                return coin, data
        finally:
            await release_semaphore(redis, "binance_api_semaphore")

    def sync_db_update(coin, candles_list):
        with transaction.atomic():
            obj, created = AllCandlesUSDT.objects.select_for_update().update_or_create(
                symbol=coin,
                defaults={field_db: candles_list}
            )

    async def main():
        logger.info(f"Starting task: get_ticker_all_pairs_usdt_{field_db}")
        try:
            redis = await aioredis.from_url(env.str('REDIS_URL'))
            symbol_list = await sync_to_async(SymbolList.objects.get)(id=1)
            coins = symbol_list.symbols.split(',')

            async with aiohttp.ClientSession() as session:
                tasks = []
                for coin in coins:
                    url = BinanceAPIUrl.generate_klines_url(start_time=start_time, end_time=end_time, symbol=coin,
                                                            interval=interval, limit=limit)
                    tasks.append(fetch_data(session, url, coin, redis))

                responses = await asyncio.gather(*tasks)
                for result in responses:
                    if result:
                        coin, data = result
                        candles_list = [{
                            'open_time': int(candles[0]),
                            'open_price': round(float(candles[1]), 6),
                            'high_price': round(float(candles[2]), 6),
                            'low_price': round(float(candles[3]), 6),
                            'close_price': round(float(candles[4]), 6),
                            'volume': round(float(candles[5]), 6),
                            'close_time': int(candles[6]),
                            'base_asset_volume': round(float(candles[7]), 6),
                            'count': int(candles[8]),
                            'taker_buy_volume': round(float(candles[9]), 6),
                            'taker_buy_base_asset_volume': round(float(candles[10]), 6),
                            'indicators': {
                                'ATR': round(float(TradingIndicators.calculate_atr(
                                    high=round(float(candles[2]), 6),
                                    low=round(float(candles[3]), 6),
                                    open_price=round(float(candles[1]), 6)
                                )), 6),
                                'TP': round(float(TradingIndicators.calculate_tp(
                                    high=round(float(candles[2]), 6),
                                    low=round(float(candles[3]), 6),
                                    close=round(float(candles[4]), 6)
                                )), 6),
                            }
                        } for candles in data]

                        await sync_to_async(sync_db_update)(coin, candles_list)

                        # await sync_to_async(AllCandlesUSDT.objects.update_or_create)(
                        #     symbol=coin,
                        #     defaults={field_db: candles_list}
                        # )

            logger.info(f"Completed task: get_ticker_all_pairs_usdt_{field_db}")
            await redis.close()

        except Exception as e:
            logger.error(f"An error occurred: {e}")

    async_to_sync(main)()




@shared_task
def analyze_all_candles_usdt():
    async def process_record(record):
        # Добавьте логику обработки записи здесь
        print(f"Record: {record.id}")

    async def fetch_all_records():
        records = await sync_to_async(list)(AllCandlesUSDT.objects.all())
        return records

    async def main():
        records = await fetch_all_records()
        tasks = []
        for record in records:
            tasks.append(process_record(record))
        await asyncio.gather(*tasks)

    async_to_sync(main)()





# # запуск задач после запуска Celery
# # @worker_ready.connect
# # def at_startup(sender, **kwargs):
# #     start_time = None
# #     end_time = None
# #     field_db = 'all_candles_5m_in_24hr'
# #     interval = '5m'
# #     limit = 288
# #
# #     # Запустите задачу с параметрами
# #     get_ticker_all_pairs_usdt_candles_by_parameters.apply_async(args=(start_time, end_time, field_db, interval, limit))
#
#
#
#
#
#
