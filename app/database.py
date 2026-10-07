from sqlalchemy.orm import (
    DeclarativeBase, 
    Mapped, 
    mapped_column,
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs, 
    create_async_engine, 
    async_sessionmaker,
)
from sqlalchemy import func

from typing import Annotated
from datetime import datetime

from app.config import get_db_url


DATABASE_URL = get_db_url()

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(),
                                                onupdate=func.now())]


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
