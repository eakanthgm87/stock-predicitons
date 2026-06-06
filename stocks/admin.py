from django.contrib import admin
from .models import Stock, HistoricalPrice, Watchlist, Prediction

admin.site.register(Stock)
admin.site.register(HistoricalPrice)
admin.site.register(Watchlist)
admin.site.register(Prediction)
