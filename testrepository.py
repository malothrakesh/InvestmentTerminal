from repositories.price_repository import PriceRepository
from services.price_service import PriceService

price_repo = PriceRepository(db)

price_service = PriceService(
    repository=price_repo,
    stock_repository=stock_repo,
)