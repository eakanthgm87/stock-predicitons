from django.core.management.base import BaseCommand
import yfinance as yf
from stocks.models import Stock, HistoricalPrice
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetch historical price data for ticker and save to DB'

    def add_arguments(self, parser):
        parser.add_argument('ticker')
        parser.add_argument('--start', default='2015-01-01')
        parser.add_argument('--end', default=None)

    def handle(self, *args, **options):
        ticker = options['ticker']
        start = options['start']
        end = options['end']
        self.stdout.write(f'Fetching {ticker} from {start} to {end or "today"}')
        data = yf.download(ticker, start=start, end=end)
        if data.empty:
            self.stdout.write('No data fetched')
            return
        stock, _ = Stock.objects.get_or_create(ticker=ticker)
        for date, row in data.iterrows():
            HistoricalPrice.objects.update_or_create(
                stock=stock,
                date=date.date(),
                defaults={'open': row['Open'], 'high': row['High'], 'low': row['Low'], 'close': row['Close'], 'volume': row.get('Volume', 0)}
            )
        self.stdout.write(f'Saved {len(data)} rows for {ticker}')
