import os
from pprint import pprint
from typing import Any, Coroutine
import django
import asyncio
import talib
import pandas as pd
import numpy as np
from asgiref.sync import sync_to_async
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from apps.celery_screening.models import AllCandlesUSDT, IndicatorATR

from modules.indicators import atr



async def main():
    all_objects = await sync_to_async(lambda qs: list(qs))(AllCandlesUSDT.objects.all())
    exampl = await atr(data=all_objects, field='all_candles_5m_in_24hr', period=14)
    pprint(exampl)

if __name__ == "__main__":
    asyncio.run(main())