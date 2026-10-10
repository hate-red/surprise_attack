from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database import Base


class Position(Base):
    __tablename__ = 'positions'

    # код КТРУ
    id: Mapped[str] = mapped_column(primary_key=True)    
    name: Mapped[str]

    okpd2: Mapped['OKPD2'] = relationship('OKPD2', back_populates='positions')
    okeis: Mapped[list['OKEI']] = relationship('OKEI', back_populates='positions')

    characteristics: Mapped[list['Characteristic']] = relationship('Characteristic', back_populates='position')


class OKPD2(Base):
    __tablename__ = 'okpd2'

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]


class OKEI(Base):
    __tablename__ = 'okei'

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]


class Characteristic(Base):
    __tablename__ = 'characteristics'

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    required: Mapped[bool] = mapped_column(default=True)
    values: Mapped[list['CharacteristicValue']] = relationship('CharacteristicValue', back_populates='characteristic')


class CharacteristicValue(Base):
    __tablename__ = 'characteristic_values'

    id: Mapped[str] = mapped_column(primary_key=True)
    
    is_range: Mapped[bool] = mapped_column(default=False)
    min_value: Mapped[float] = mapped_column(nullable=True)
    max_value: Mapped[float] = mapped_column(nullable=True)
    
    is_quality: Mapped[bool] = mapped_column(default=False)
    quality_description: Mapped[str] = mapped_column(nullable=True)
    
    okeis: Mapped[list['OKEI']] = relationship('OKEI', back_populates='characteristic_values')
