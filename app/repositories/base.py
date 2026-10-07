from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session_maker


class BaseRepository:
    """
    Класс с базовыми методами для работы с базой данных. 
    Для использования необходимо наследоваться. 
    При необходимости изменить поведение можно добавить либо переопределить методы.
    Наследоваться так:
    ```
    class UserRepository(BaseRepository):
        model = User
    ```
    """
    model = None


    @classmethod
    async def get_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by) # type: ignore
            result = await session.execute(query)
        
            return result.scalar_one_or_none()


    @classmethod
    async def filter(cls, **filter_by) -> list:
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by) # type: ignore
            result = await session.execute(query)
        
            return result.scalars().all() # type: ignore


    @classmethod
    async def create_one(cls, **values) -> None:
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values) # type: ignore
                session.add(new_instance)

                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e

                return new_instance


    @classmethod
    async def delete(cls, instance) -> None:
        async with async_session_maker() as session:
                async with session.begin():
                    query = delete(cls.model).filter_by(**filter_by) # type: ignore
                    result = await session.execute(query)
                    
                    try:
                        await session.commit()
                    except SQLAlchemyError as e:
                        await session.rollback()
                        raise e
                    
                    return result.rowcount # type: ignore
