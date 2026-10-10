from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.additional_characteristics import Category, AdditionalCharacteristic
from app.database import async_session_maker


class CategoryRepository(BaseRepository):
    model = Category


class AdditionalCharacteristicRepository(BaseRepository):
    model = AdditionalCharacteristic
