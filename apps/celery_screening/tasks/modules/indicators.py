from pprint import pprint

import pandas as pd
import talib
import numpy as np

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


async def atr(data, field='all_candles_1mo_in_1y', format_data=None, coind=None, period=14):  # -> dict[str, list[float]]:
    data_input = ConverterData(data)
    converted_data = await data_input.for_atr(field)
    results = {}  # Будем собирать итоговый словарь
    for symbol_data in converted_data:
        symbol = symbol_data['symbol']

        # Преобразуем списки значений в Series
        high_series  = pd.Series(symbol_data['high_price']).astype(float)
        low_series   = pd.Series(symbol_data['low_price']).astype(float)
        close_series = pd.Series(symbol_data['close_price']).astype(float)

        # Вычисляем ATR для данного символа
        atr_data = talib.ATR(high_series, low_series, close_series, timeperiod=period)
        # Исключаем NaN значения
        indicators_atr = atr_data[~np.isnan(atr_data)]
        indicators_atr_rounded = [round(x, 10) for x in indicators_atr]
        # Добавляем результат в словарь, преобразуя Series в список

        results[symbol] = np.array(indicators_atr_rounded).tolist()




    return results
