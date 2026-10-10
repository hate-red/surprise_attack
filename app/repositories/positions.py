from app.repositories.base import BaseRepository
from app.models.positions import (
    Position,
    OKEI,
    Characteristic,
    CharacteristicValue
)


class PositionRepository(BaseRepository):
    model = Position


class OKEIRepository(BaseRepository):
    model = OKEI


class CharacteristicRepositroy(BaseRepository):
    model = Characteristic


class CharacteristicValueRepository(BaseRepository):
    model = CharacteristicValue
