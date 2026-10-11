from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.additional_characteristics import Category, AdditionalCharacteristic
from app.database import async_session_maker


class CategoryRepository(BaseRepository):
    model = Category


class AdditionalCharacteristicRepository(BaseRepository):
    model = AdditionalCharacteristic

    @classmethod
    async def get_all_with_categories(cls) -> list[tuple[str, str, str, str | None]]:
        """(категория, характеристика, тип, единица) для словаря СТЕ."""
        async with async_session_maker() as session:
            stmt = (
                select(
                    Category.name,
                    AdditionalCharacteristic.name,
                    AdditionalCharacteristic.kind,
                    AdditionalCharacteristic.measure_units,
                )
                .join(Category, Category.id == AdditionalCharacteristic.category_id)
            )
            result = await session.execute(stmt)
            return list(result.all())
