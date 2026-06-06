from rest_framework import serializers
from .models import Stock, HistoricalPrice, Watchlist, Prediction

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

class HistoricalPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalPrice
        fields = '__all__'

class WatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watchlist
        fields = '__all__'

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = '__all__'
