import os
import django
import asyncio
import talib
import pandas as pd
import numpy as np
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.celery_screening.models import AllCandlesUSDT, IndicatorATR


class CoinIndicators:
    def __init__(self, candles_ticks):
        self.candles_ticks = candles_ticks

    async def sma(self, **kwargs):
        ...

    async def ema(self):
        ...
    async def bbands(self):
        ...
    async def atr(self, period=14):

        ...








    async def rsi(self):
        ...
    async def stochastic_oscillator(self):
        ...
    async def macd(self):
        ...
    async def adx(self):
        ...
    async def sar(self):
        ...
    async def vwap(self):
        ...
    async def ad_line(self):
        ...

    async def cell_indicator(self, candles, indicator):
        if hasattr(self,indicator):
            method = getattr(self, indicator)
            method(candles)
        else:
            print(f"Indicator {indicator} not found.")













    async def get_list_indicators_in_period(self, period, indicator) -> dict:
        dict_indicators = {}
        for period_candles_ticks in self.candles_ticks:
            if period in period_candles_ticks:
                candl_list = period_candles_ticks[period]
                list_indicators = [candl['indicators'][indicator] for candl in candl_list]
                dict_indicators[period_candles_ticks['symbol']] = list_indicators
            else:
                print(f"Key '{period}' not found in {period_candles_ticks['symbol']}")
        return dict_indicators

    async def indicator_variation_coefficient(self, period, indicator):
        print(period, indicator)
        dict_indicators = await self.get_list_indicators_in_period(period, indicator)
        index_dict = {}
        # ATR_index_dict = {}
        for symbol, list_indicators in dict_indicators.items():
            filtered_list_indicators = [value for value in list_indicators if value > 0]
            if filtered_list_indicators:
                min_atr = float(np.min(filtered_list_indicators))
                max_atr = float(np.max(filtered_list_indicators))
                mean_atr = float(np.mean(filtered_list_indicators))

            else:
                min_atr = max_atr = mean_atr = 0.0

            # Вычисление коэффициента вариации
            if mean_atr != 0:
                volatility_index = (max_atr - min_atr) / mean_atr

            else:
                volatility_index = 0

            dict_indicators[symbol] = {
                f'min_{indicator}': round(min_atr, 6),
                f'max_{indicator}': round(max_atr, 6),
                f'mean_{indicator}': round(mean_atr, 6),
                'index': round(volatility_index, 6),
            }
            index_dict[symbol] = dict_indicators[symbol]['index']

        print(len(filtered_list_indicators))
        return index_dict




    @staticmethod
    async def save_indicators_to_db(period, indicator, indicators):
        field_name = period.replace("all_candles_", "atr_coefficient_")

        for symbol, values in indicators.items():
            try:
                indicator_atr, created = await sync_to_async(IndicatorATR.objects.update_or_create)(
                    symbol=symbol,
                    defaults={field_name: values}
                )
                if not created:
                    setattr(indicator_atr, field_name, values)
                    await sync_to_async(indicator_atr.save)()
            except Exception as e:
                print(f"Error saving {symbol}: {e}")
    entitie


    async def display_and_save_indicators(self, period, indicator, save_to_db=True):
        indicators = await self.indicator_variation_coefficient(period, indicator)
        print(indicators)
        if save_to_db:
            await self.save_indicators_to_db(period, indicator, indicators)



async def main():
    all_objects = await sync_to_async(list)(AllCandlesUSDT.objects.all())
    data_list = [
        {
            'id': obj.id,
            'symbol': obj.symbol,
            'all_candles_5m_in_24hr': obj.all_candles_5m_in_24hr,
            'all_candles_1hr_in_24hr': obj.all_candles_1hr_in_24hr,
            'all_candles_1d_in_1mo': obj.all_candles_1d_in_1mo,
            'all_candles_1mo_in_1y': obj.all_candles_1mo_in_1y,
        }
        for obj in all_objects
    ]

    coin_print_list = CoinIndicators(data_list)
    await coin_print_list.display_and_save_indicators('all_candles_5m_in_24hr', 'ATR')
    await coin_print_list.display_and_save_indicators('all_candles_1hr_in_24hr', 'ATR')
    await coin_print_list.display_and_save_indicators('all_candles_1d_in_1mo', 'ATR')
    await coin_print_list.display_and_save_indicators('all_candles_1mo_in_1y', 'ATR')

if __name__ == "__main__":
    asyncio.run(main())





