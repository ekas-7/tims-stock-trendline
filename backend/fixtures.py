from .extensions import db, StockPrice
import time

from datetime import datetime, timedelta
import random


def delete_stock_prices():
    """Delete all the stock prices in the database. DO NOT USE IN PRODUCTION."""
    StockPrice.query.delete()
    db.session.commit()


def load_slow_fixtures(count: int = 1000):
    """Mock stock prices in the database with a delay of 1 second between each record."""
    delete_stock_prices()
    reference_date = datetime.strptime("2021-01-01", "%Y-%m-%d")

    # Create the stock price records
    for i in range(count):
        price = random.uniform(100, 200)
        created_at = reference_date + timedelta(minutes=i)
        stock_price = StockPrice(price=price, created_at=created_at)
        db.session.add(stock_price)
        db.session.commit()
        print(f"Added new stock entry at ID: {stock_price.id}")
        time.sleep(1)
