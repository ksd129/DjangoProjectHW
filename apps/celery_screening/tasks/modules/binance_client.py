import urllib

from core.settings import env


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
