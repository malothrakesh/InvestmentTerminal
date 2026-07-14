from database.session import SessionLocal
from database.models import Stock, Price

from sqlalchemy import select



def main():
    db = SessionLocal()

    print("\nStocks")
    print("-" * 50)
    for stock in db.query(Stock).all():
        print(stock)

    print("\nPrices")
    print("-" * 50)
    for price in db.query(Price).all():
        print(price)

    stocks = db.scalars(select(Stock)).all()
    prices = db.scalars(select(Price)).all()

    for stock in stocks:
        print(stock)

    for price in prices:
        print(price)

    db.close()


if __name__ == "__main__":
    main()