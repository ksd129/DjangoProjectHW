import os
import json
from pprint import pprint
from typing import Any, Coroutine
import django
import asyncio
import requests
import talib
import pandas as pd
import numpy as np
from asgiref.sync import sync_to_async

from core import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from apps.celery_screening.models import AllCandlesUSDT, IndicatorATR
from apps.celery_screening.tasks.modules.binance_client import BinanceAPIUrl

from modules.indicators import atr


async def save_to_json(data, filename="all_objects.json"):
    serialized_data = [obj.__dict__ for obj in data]  # Преобразуем объекты в словари
    for item in serialized_data:
        item.pop('_state', None)  # Удаляем служебные данные Django

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(serialized_data, f, ensure_ascii=False, indent=4)



async def main():
    data_from_db = await sync_to_async(lambda qs: list(qs))(AllCandlesUSDT.objects.all())
    # exampl = await atr(data=all_objects, field='all_candles_1mo_in_1y', format_data='from_db', period=10)
    # pprint(exampl)
    symbol = 'SNTUSDT'
    url = BinanceAPIUrl.generate_klines_url(symbol=symbol,
                                            start_time=1744074000000,
                                            end_time=1744160400000,
                                            interval='3m',
                                            limit=480)
    response = requests.get(url)
    data_response = response.json()
    atr_indicators = await atr(data=data_response, format_data='from_api', coind=symbol, period=24)
    print(url)
    pprint(f': {[i for i in atr_indicators[symbol]]}', width=120)

# f"{i['percent change']} - {i['time_open']}"


if __name__ == "__main__":
    asyncio.run(main())