from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Stock(models.Model):
    ticker = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.ticker

class HistoricalPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('stock', 'date')
        ordering = ['date']

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100, default='My Watchlist')
    stocks = models.ManyToManyField(Stock, related_name='in_watchlists')

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Prediction(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='predictions')
    created_at = models.DateTimeField(auto_now_add=True)
    horizon_days = models.IntegerField()
    predicted_prices = models.JSONField()
    model_version = models.CharField(max_length=100, blank=True)

class PortfolioHolding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="holdings")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="holdings")
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.stock.ticker} ({self.quantity})"


class Transaction(models.Model):
    ACTIONS = (
        ("BUY", "BUY"),
        ("SELL", "SELL"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="transactions")
    action = models.CharField(max_length=4, choices=ACTIONS)
    quantity = models.IntegerField()
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.action} {self.quantity} {self.stock.ticker} @ {self.price}"
