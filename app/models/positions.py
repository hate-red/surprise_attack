from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import NUMRANGE, Range

from app.database import Base


position_okei = Table(
    "position_okei",
    Base.metadata,
    Column("position_id", ForeignKey("positions.id"), primary_key=True),
    Column("okei_id", ForeignKey("okei.id"), primary_key=True),
)

characteristic_value_okei = Table(
    "characteristic_value_okei",
    Base.metadata,
    Column(
        "characteristic_value_id",
        ForeignKey("characteristic_values.id"),
        primary_key=True,
    ),
    Column("okei_id", ForeignKey("okei.id"), primary_key=True),
)


# Типы и виды характеристик КТРУ (поля <type>, <kind>, <choiceType> выгрузки).
CHARACTERISTIC_TYPE_QUALITATIVE = 1   # качественная (перечень значений)
CHARACTERISTIC_TYPE_QUANTITATIVE = 2  # количественная (число / диапазон)


class Position(Base):
    __tablename__ = "positions"

    # код КТРУ
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]

    # Метаданные позиции из выгрузки nsiKTRUNew (все поля добавлены миграцией
    # 2b7c4e91d0aa и допускают NULL, чтобы старые данные оставались валидными).
    okpd2_code: Mapped[str | None] = mapped_column(nullable=True, index=True)
    okpd2_name: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str | None] = mapped_column(nullable=True)
    version: Mapped[int | None] = mapped_column(nullable=True)
    is_template: Mapped[bool] = mapped_column(default=False, server_default="false")
    parent_code: Mapped[str | None] = mapped_column(nullable=True)
    application_date_start: Mapped[datetime | None] = mapped_column(nullable=True)
    application_date_end: Mapped[datetime | None] = mapped_column(nullable=True)
    rubricators: Mapped[str | None] = mapped_column(nullable=True)

    okeis: Mapped[list["OKEI"]] = relationship(
        secondary=position_okei,
        back_populates="positions",
    )
    characteristics: Mapped[list["Characteristic"]] = relationship(
        back_populates="position",
        cascade="all, delete-orphan",
    )


class OKEI(Base):
    __tablename__ = "okei"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    # код ОКЕИ ("796" — штука, "006" — метр ...)
    code: Mapped[str | None] = mapped_column(nullable=True, unique=True)

    positions: Mapped[list["Position"]] = relationship(
        secondary=position_okei,
        back_populates="okeis",
    )
    characteristic_values: Mapped[list["CharacteristicValue"]] = relationship(
        secondary=characteristic_value_okei,
        back_populates="okeis",
    )


class Characteristic(Base):
    __tablename__ = "characteristics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    required: Mapped[bool] = mapped_column(default=True)

    # код характеристики в КТРУ и её тип/вид из выгрузки
    code: Mapped[str | None] = mapped_column(nullable=True)
    char_type: Mapped[int | None] = mapped_column(nullable=True)
    kind: Mapped[int | None] = mapped_column(nullable=True)
    choice_type: Mapped[int | None] = mapped_column(nullable=True)

    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"), index=True)
    position: Mapped["Position"] = relationship(back_populates="characteristics")

    values: Mapped[list["CharacteristicValue"]] = relationship(
        back_populates="characteristic",
        cascade="all, delete-orphan",
    )


class CharacteristicValue(Base):
    __tablename__ = "characteristic_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    measure_units: Mapped[str] = mapped_column(nullable=True)

    is_range: Mapped[bool] = mapped_column(default=False)
    range: Mapped[Range[float]] = mapped_column(NUMRANGE, nullable=True)

    is_quality: Mapped[bool] = mapped_column(default=False)
    quality_description: Mapped[str | None] = mapped_column(nullable=True)

    # точное числовое значение (<valueSet><concreteValue>) и код значения КТРУ
    concrete_value: Mapped[Decimal | None] = mapped_column(nullable=True)
    value_code: Mapped[str | None] = mapped_column(nullable=True)
    value_format: Mapped[str | None] = mapped_column(nullable=True)

    characteristic_id: Mapped[int] = mapped_column(
        ForeignKey("characteristics.id"), index=True
    )
    characteristic: Mapped["Characteristic"] = relationship(
        back_populates="values"
    )

    okeis: Mapped[list["OKEI"]] = relationship(
        secondary=characteristic_value_okei,
        back_populates="characteristic_values",
    )
