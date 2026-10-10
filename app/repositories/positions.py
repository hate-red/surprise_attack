from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.positions import (
    Position,
    OKEI,
    Characteristic,
    CharacteristicValue
)
from app.database import async_session_maker


class PositionRepository(BaseRepository):
    model = Position

    @classmethod
    async def get_one_by_id(cls, id):
        async with async_session_maker() as session:
            stmt = (
                select(Position)
                .where(Position.id == id)
                .options(
                    selectinload(Position.okeis),
                    selectinload(Position.characteristics)
                        .selectinload(Characteristic.values)
                        .selectinload(CharacteristicValue.okeis),
                )
            )

            result = await session.execute(stmt)
            position = result.scalar_one_or_none()
            return position


class OKEIRepository(BaseRepository):
    model = OKEI


class CharacteristicRepositroy(BaseRepository):
    model = Characteristic


class CharacteristicValueRepository(BaseRepository):
    model = CharacteristicValue
