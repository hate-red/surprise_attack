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


class Position(Base):
    __tablename__ = "positions"

    # код КТРУ
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]

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

    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"))
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

    characteristic_id: Mapped[int] = mapped_column(
        ForeignKey("characteristics.id")
    )
    characteristic: Mapped["Characteristic"] = relationship(
        back_populates="values"
    )

    okeis: Mapped[list["OKEI"]] = relationship(
        secondary=characteristic_value_okei,
        back_populates="characteristic_values",
    )
