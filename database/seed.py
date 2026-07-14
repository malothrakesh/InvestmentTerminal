from database.session import SessionLocal
from database.models import Stock, Price
from datetime import datetime


def seed_data():
    db = SessionLocal()

    try:
        stock = Stock(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            exchange="NASDAQ",
            currency="USD",
        )

        db.add(stock)
        db.flush()

        price = Price(
            stock_id=stock.id,
            trade_date=datetime.utcnow(),
            open=180,
            high=185,
            low=179,
            close=183,
            volume=1000000,
        )

        db.add(price)
        db.commit()

    finally:
        db.close()