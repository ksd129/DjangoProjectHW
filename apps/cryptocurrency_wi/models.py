from django.core.validators import MinValueValidator, MaxValueValidator

from django.db import models

class CriptoCoin(models.Model):
    coin = models.CharField(max_length=4)
    short_title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.coin

    def get_age(self):
        """
        Calculate and return the age of the CriptoCoin instance.
    
        This method computes the time difference between the current time and the
        creation time of the CriptoCoin instance, returning a formatted string
        representing the age in days, hours, minutes, and seconds.
    
        Returns:
            str: A formatted string representing the age of the CriptoCoin instance
                 in the format "X дней, HH:MM:SS", where X is the number of days,
                 HH is hours (0-23), MM is minutes (00-59), and SS is seconds (00-59).
        """
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days} дней, {hours}:{minutes:02}:{seconds:02}"


class CoinInfo(models.Model):
    """
    Represents detailed information about a cryptocurrency coin.

    This model stores various attributes and metrics related to a specific cryptocurrency,
    including its rank, capitalization, and price information.

    Attributes:
        cripto_coin (ForeignKey): Reference to the associated CriptoCoin instance.
        title (str): The full name or title of the cryptocurrency.
        rank (int): The ranking of the cryptocurrency (1-100).
        capitalization (float): The market capitalization of the cryptocurrency.
        diluted_valuation (float): The fully diluted valuation of the cryptocurrency.
        dominance (float): The market dominance percentage of the cryptocurrency.
        circulating_offer (float): The number of coins currently in circulation.
        max_price (float): The highest recorded price of the cryptocurrency.
        min_price (float): The lowest recorded price of the cryptocurrency.
        created_at (datetime): The timestamp when this record was created.
    """

    cripto_coin = models.ForeignKey(CriptoCoin, on_delete=models.CASCADE)
    title = models.CharField(max_length=2000)
    rank = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    capitalization = models.FloatField()
    diluted_valuation = models.FloatField()
    dominance = models.FloatField()
    circulating_offer = models.FloatField()
    max_price = models.FloatField()
    min_price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a string representation of the CoinInfo instance.

        Returns:
            str: The title of the cryptocurrency.
        """
        return self.title


