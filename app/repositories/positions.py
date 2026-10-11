from sqlalchemy import func, select
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

    @classmethod
    async def get_many_by_ids(cls, ids: list[str]) -> list[Position]:
        """Позиции с характеристиками и значениями (формат PositionResponse)."""
        if not ids:
            return []
        async with async_session_maker() as session:
            stmt = (
                select(Position)
                .where(Position.id.in_(ids))
                .options(
                    selectinload(Position.okeis),
                    selectinload(Position.characteristics)
                        .selectinload(Characteristic.values)
                        .selectinload(CharacteristicValue.okeis),
                )
            )
            result = await session.execute(stmt)
            by_id = {p.id: p for p in result.scalars().all()}
            return [by_id[i] for i in ids if i in by_id]

    @classmethod
    async def get_index_rows(cls) -> list[tuple]:
        """Лёгкие данные всех позиций для индекса наименований (без характеристик)."""
        async with async_session_maker() as session:
            stmt = select(
                Position.id,
                Position.name,
                Position.okpd2_code,
                Position.okpd2_name,
                Position.is_template,
                Position.application_date_start,
                Position.application_date_end,
                Position.parent_code,
            )
            result = await session.execute(stmt)
            return list(result.all())

    @classmethod
    async def get_characteristic_rows(cls, position_ids: list[str]) -> list[tuple]:
        """Характеристики и значения кандидатов одним запросом (без ORM-объектов)."""
        if not position_ids:
            return []
        async with async_session_maker() as session:
            stmt = (
                select(
                    Characteristic.id,
                    Characteristic.position_id,
                    Characteristic.name,
                    Characteristic.required,
                    Characteristic.char_type,
                    Characteristic.kind,
                    Characteristic.choice_type,
                    CharacteristicValue.id,
                    CharacteristicValue.name,
                    CharacteristicValue.measure_units,
                    CharacteristicValue.is_range,
                    CharacteristicValue.range,
                    CharacteristicValue.is_quality,
                    CharacteristicValue.quality_description,
                    CharacteristicValue.concrete_value,
                )
                .select_from(Characteristic)
                .outerjoin(
                    CharacteristicValue,
                    CharacteristicValue.characteristic_id == Characteristic.id,
                )
                .where(Characteristic.position_id.in_(position_ids))
                .order_by(Characteristic.id, CharacteristicValue.id)
            )
            result = await session.execute(stmt)
            return list(result.all())

    @classmethod
    async def get_okei_names(cls, position_ids: list[str]) -> dict[str, list[str]]:
        if not position_ids:
            return {}
        from app.models.positions import position_okei

        async with async_session_maker() as session:
            stmt = (
                select(position_okei.c.position_id, OKEI.name)
                .join(OKEI, OKEI.id == position_okei.c.okei_id)
                .where(position_okei.c.position_id.in_(position_ids))
            )
            result = await session.execute(stmt)
            okeis: dict[str, list[str]] = {}
            for position_id, name in result.all():
                okeis.setdefault(position_id, []).append(name)
            return okeis

    @classmethod
    async def count(cls) -> int:
        async with async_session_maker() as session:
            result = await session.execute(select(func.count()).select_from(Position))
            return int(result.scalar_one())


class OKEIRepository(BaseRepository):
    model = OKEI


class CharacteristicRepositroy(BaseRepository):
    model = Characteristic

    @classmethod
    async def get_distinct_names(cls) -> list[tuple[str, int]]:
        """Все названия характеристик КТРУ и число позиций, где они встречаются."""
        async with async_session_maker() as session:
            stmt = select(Characteristic.name, func.count()).group_by(Characteristic.name)
            result = await session.execute(stmt)
            return list(result.all())


class CharacteristicValueRepository(BaseRepository):
    model = CharacteristicValue

    @classmethod
    async def get_distinct_quality_values(cls) -> list[str]:
        async with async_session_maker() as session:
            stmt = (
                select(CharacteristicValue.quality_description)
                .where(CharacteristicValue.is_quality.is_(True))
                .distinct()
            )
            result = await session.execute(stmt)
            return [v for v in result.scalars().all() if v]
