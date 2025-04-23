from pprint import pprint
from datetime import datetime, timezone, timedelta
import pandas as pd
import talib
import numpy as np

from zoneinfo import ZoneInfo
from django.conf import settings

np.set_printoptions(suppress=True,
                    precision=10,
                    formatter={'float_kind': lambda x: format(x, '.10f')})

class ConverterData:
    def __init__(self, initial_data):
        self.data = initial_data

    @staticmethod
    async def extract_data(obj):
        # Это асинхронный метод, если требуется выполнение потенциально затратных операций.
        return {
            'id': obj.id,
            'symbol': obj.symbol,
            'all_candles_5m_in_24hr': obj.all_candles_5m_in_24hr,
            'all_candles_1hr_in_24hr': obj.all_candles_1hr_in_24hr,
            'all_candles_1d_in_1mo': obj.all_candles_1d_in_1mo,
            'all_candles_1mo_in_1y': obj.all_candles_1mo_in_1y,
        }

    async def for_atr(self, field):

        data_con = [await self.extract_data(obj) for obj in self.data]

        data_atr = [
            {
                'symbol': data['symbol'],
                'high_price': [candl['high_price'] for candl in data[field]],
                'low_price': [candl['low_price'] for candl in data[field]],
                'close_price': [candl['close_price'] for candl in data[field]],

            }
            for data in data_con
        ]

        return data_atr

LOCAL_TIMEZONE = ZoneInfo("Europe/Kyiv")

def convert_timestamp(timestamp):
    if timestamp is None:
        return "Unknown"

    dt_utc = datetime.fromtimestamp(timestamp / 1000, tz=ZoneInfo("UTC"))
    dt_local = dt_utc.astimezone(LOCAL_TIMEZONE)  # Переводим в локальный часовой пояс

    return dt_local.strftime('%Y-%m-%d %H:%M:%S'), timestamp

async def atr(data, field='all_candles_1mo_in_1y', format_data=None, coind=None, period=14) -> dict[str, list[dict]]:
    """
    Функция для вычисления индикатора ATR (Average True Range) на основе полученных данных.

    :param data: Список данных, полученных из API или базы данных.
    :param field: Поле, которое нужно обработать.
    :param format_data: Формат данных ('from_api' или 'from_db').
    :param coind: Символ монеты.
    :param period: Период для расчета ATR.
    :return: Словарь с результатами.
    """
    results = {}

    def calculate_atr(data_entries, symbol):
        high_prices  = [entry["high_price"] for entry in data_entries]
        low_prices   = [entry["low_price"] for entry in data_entries]
        close_prices = [entry["close_price"] for entry in data_entries]
        time_open    = [convert_timestamp(entry.get("timestamp")) for entry in data_entries]  # Проверяем наличие ключа

        high_series  = pd.Series(high_prices).astype(float)
        low_series   = pd.Series(low_prices).astype(float)
        close_series = pd.Series(close_prices).astype(float)

        atr_values = talib.ATR(high_series, low_series, close_series, timeperiod=period)
        indicators_atr = atr_values[~np.isnan(atr_values)]

        results[symbol] = [
        {
            "time_open": time_open[i + period - 1],  # Смещаем индекс
            "ATR": round(atr, 10),
            "percent change": float(round(((atr - indicators_atr.iloc[i - 1]) / indicators_atr.iloc[i - 1]) * 100, 2)) if i > 0 else None,
            "high_prices": high_prices[i + period - 1]  # Смещаем индекс
        }
        for i, atr in enumerate(indicators_atr)
    ]

    if format_data == 'from_api' and isinstance(data, list):
        processed_data = [
            {
                "timestamp": entry[0],
                "open_price": float(entry[1]),
                "high_price": float(entry[2]),
                "low_price": float(entry[3]),
                "close_price": float(entry[4])
            } for entry in data
        ]

        calculate_atr(processed_data, coind)

    elif format_data == 'from_db':
        data_input = ConverterData(data)
        converted_data = await data_input.for_atr(field)

        for symbol_data in converted_data:
            entries = [
                {"timestamp": None, "high_price": h, "low_price": l, "close_price": c}
                for h, l, c in zip(symbol_data['high_price'], symbol_data['low_price'], symbol_data['close_price'])
            ]
            calculate_atr(entries, symbol_data['symbol'])

    return results


