from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    characteristics: Mapped[list['AdditionalCharacteristic']] = relationship(back_populates='categories')


class AdditionalCharacteristic(Base):
    __tablename__ = 'additional_characteristics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    kind: Mapped[str]
    measure_units: Mapped[str]

    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    category: Mapped['Category'] = relationship(back_populates='characteristics')
