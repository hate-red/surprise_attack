from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass

@dataclass
class User:
    id: int | None = None
    name: str | None = None

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # CREATE — добавить нового пользователя
    async def add(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()       # отправит INSERT и заполнит user.id
        return user

    # READ — прочитать по id или список
    async def get(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def list(self, limit: int = 20) -> list[User]:
        res = await self.db.execute(select(User).limit(limit))
        return list(res.scalars().all())

    # UPDATE — меняем атрибут загруженного объекта
    async def rename(self, user: User, name: str) -> User:
        user.name = name            # ORM сам заметит изменение («объект грязный»)
        await self.db.flush()
        return user

    # DELETE
    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()