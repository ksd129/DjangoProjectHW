from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class CustomDecimalField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_digits', 30)
        kwargs.setdefault('decimal_places', 10)
        kwargs.setdefault('validators', [MinValueValidator(0)])
        super().__init__(*args, **kwargs)


class BaseTickerModelSymbol(models.Model):
    symbol = models.CharField(max_length=20, unique=True, db_index=True)

    class Meta:
        abstract = True

class BaseTickerModel(BaseTickerModelSymbol):
    open_time = models.BigIntegerField(db_index=True, default=0)
    open_price = CustomDecimalField(default=Decimal('0.0'))
    high_price = CustomDecimalField(default=Decimal('0.0'))
    low_price = CustomDecimalField(default=Decimal('0.0'))
    volume = CustomDecimalField(default=Decimal('0.0'))
    close_time = models.BigIntegerField(db_index=True, default=0)
    count = models.BigIntegerField()

    class Meta:
        abstract = True



class Ticker24hrUSDT(BaseTickerModel):
    """
symbol: Символ торговой пары (например, "BTCUSDT").
price_change: Изменение цены за последние 24 часа.
price_change_percent: Процентное изменение цены за последние 24 часа.
weighted_avg_price: Средневзвешенная цена за последние 24 часа.
prev_close_price: Цена закрытия предыдущих торгов.
last_price: Последняя цена сделки.
last_qty: Количество последней сделки.
bid_price: Лучшая цена покупателя (bid).
bid_qty: Объём в заявке на покупку по лучшей цене (bid).
ask_price: Лучшая цена продавца (ask).
ask_qty: Объём в заявке на продажу по лучшей цене (ask).
open_price: Цена открытия текущих торгов.
high_price: Максимальная цена за последние 24 часа.
low_price: Минимальная цена за последние 24 часа.
volume: Объём торгов за последние 24 часа.
quote_volume: Объём торгов в валюте котировки за последние 24 часа.
open_time: Время открытия текущих торгов в миллисекундах.
close_time: Время закрытия текущих торгов в миллисекундах.
first_id: ID первой сделки за последние 24 часа.
last_id: ID последней сделки за последние 24 часа.
count: Количество сделок за последние 24 часа.
    """
    # symbol = models.CharField(max_length=20, unique=True, db_index=True)
    price_change = CustomDecimalField()
    price_change_percent = models.DecimalField(max_digits=30, decimal_places=5)
    weighted_avg_price = CustomDecimalField()
    prev_close_price = CustomDecimalField()
    last_price = CustomDecimalField()
    last_qty = models.BigIntegerField(validators=[MinValueValidator(0)])
    bid_price = CustomDecimalField()
    bid_qty = models.BigIntegerField(validators=[MinValueValidator(0)])
    ask_price = CustomDecimalField()
    ask_qty = models.BigIntegerField(validators=[MinValueValidator(0)])
    quote_volume = models.DecimalField(max_digits=35, decimal_places=15, validators=[MinValueValidator(0)])
    first_id = models.BigIntegerField()
    last_id = models.BigIntegerField()


    def __str__(self):
        return self.symbol

class Candles1mUSDT(BaseTickerModel):
    close_price = CustomDecimalField(default=Decimal('0.0'))
    base_asset_volume = CustomDecimalField(max_digits=20, decimal_places=10)
    taker_buy_volume = CustomDecimalField(max_digits=20, decimal_places=10)
    taker_buy_base_asset_volume = CustomDecimalField(max_digits=20, decimal_places=10)

    def __str__(self):
        return f'{self.symbol}: {self.open_time} - {self.close_time}'

    class Meta:
        indexes = [
            models.Index(fields=['symbol', 'open_time']),
        ]

class AllCandlesUSDT(BaseTickerModelSymbol):
    all_candles_5m_in_24hr = models.JSONField(default=list)
    all_candles_1hr_in_24hr = models.JSONField(default=list)
    all_candles_1d_in_1mo = models.JSONField(default=list)
    all_candles_1mo_in_1y = models.JSONField(default=list)

    def __str__(self):
        return self.symbol




class SymbolList(models.Model):
    coin_filter = models.CharField(max_length=200, default='default_filter')
    symbols = models.TextField()

    def __str__(self):
        return self.coin_filter