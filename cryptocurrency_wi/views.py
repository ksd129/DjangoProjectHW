from django.shortcuts import render

from .models import CriptoCoin, CoinInfo


# Create your views here.
def index(request):
    coins = CriptoCoin.objects.all()
    coin_info = CoinInfo.objects.all()
    return render(request, 'binance_html/coins.html', {'coins': coins, 'coin_info': coin_info})


def single_coin(request, cripto_coin):
    cripto_coin = cripto_coin.upper()
    try:
        coin = CriptoCoin.objects.get(coin=cripto_coin)
        try:
            coin_info = CoinInfo.objects.get(cripto_coin=coin)
        except CoinInfo.DoesNotExist:
            coin_info = f"There is no detailed information about the {cripto_coin} cryptocurrency"
    except CriptoCoin.DoesNotExist:
            coin = f"There is no information about the {cripto_coin} cryptocurrency"
            coin_info = None

    return render(request, "binance_html/coin_info.html", {'coin': coin, 'coin_info': coin_info})

def base_simple(request):
    return render(request, "binance_html/base2.html")