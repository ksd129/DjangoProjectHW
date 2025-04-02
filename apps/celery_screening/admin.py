from django.contrib import admin

from . import models

admin.site.register(models.Ticker24hrUSDT)
admin.site.register(models.AllCandlesUSDT)
