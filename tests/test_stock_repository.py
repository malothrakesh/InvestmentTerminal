from database.session import SessionLocal
from repositories.stock_repository import StockRepository


def main():
    db = SessionLocal()
    repo = StockRepository(db)

    print("Total:", repo.total_stocks())
    print("By Symbol:", repo.get_by_symbol("AAPL"))
    print("Search:", repo.search_stocks("Apple"))
    print("Sector:", repo.filter_by_sector("Technology"))
    print("Exists:", repo.symbol_exists("AAPL"))

    db.close()


if __name__ == "__main__":
    main()