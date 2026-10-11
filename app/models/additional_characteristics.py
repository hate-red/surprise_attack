from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    """Конечная категория портала поставщиков (выгрузки СТЕ, xlsx)."""

    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    characteristics: Mapped[list['AdditionalCharacteristic']] = relationship(
        back_populates='category'
    )


class AdditionalCharacteristic(Base):
    """Характеристика СТЕ из выгрузки портала поставщиков.

    Это вспомогательный источник: он помогает распознать формулировку
    пользователя, но не задаёт допустимые значения — их задаёт только КТРУ.
    """

    __tablename__ = 'additional_characteristics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    # тип характеристики из выгрузки: "Справочник", "Текст",
    # "Целое числовое значение", "Дробное числовое значение", "Признак"
    kind: Mapped[str]
    # единица измерения (после унификации); у многих характеристик её нет
    measure_units: Mapped[str | None] = mapped_column(nullable=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey('categories.id'), index=True
    )
    category: Mapped['Category'] = relationship(
        back_populates='characteristics'
    )
