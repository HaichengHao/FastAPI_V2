from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import desc, select

from src.books.models import Book
from src.books.schemas import BookCreateSchema, BookUpdateSchema
from src.db.main import get_session


class BookService:
    async def get_all_books(self, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).options(selectinload(Book.reviews)).order_by(desc(Book.published_date)) #important:解决懒加载导致的问题
        result = await session.execute(statement)
        return result.scalars().all() #tips:用scalars来拿到数据行

    async def get_a_book(self, book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).options(selectinload(Book.reviews)).where(Book.uid == book_uid)
        result = await session.execute(statement)
        return result.scalar_one_or_none() #tips:用scalar_one_or_none()来检验数据库中是否真的有图书

    async def create_books(self, book_data: BookCreateSchema,user_uid:str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).where(Book.title == book_data.title)
        result = await session.execute(statement)
        book_exist = result.scalar_one_or_none()
        if book_exist:
            return None

        new_book = Book(**book_data.model_dump())
        new_book.user_uid=user_uid
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book) #important:提交之后要记得刷新
        return new_book

    async def update_book(
        self,
        book_uid: str,
        update_data: BookUpdateSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
    ):
        book_to_update = await self.get_a_book(book_uid=book_uid, session=session)
        if book_to_update is None:
            return None

        #tips:遍历整个dump出来的字典对象，因为指定了exclude_unset,所以未设置的不用管，保持原样
        #  .items()可以返回字典的键值对，然后通过for循环遍历其中的键值对进行下一步操作
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(book_to_update, field, value) #important:要活用
            #tips:setattr(object,name,value)
            #  它可以对一个对象的键(name)设置指定的值

        await session.commit()
        await session.refresh(book_to_update)
        return book_to_update

    async def delete_book(self, book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]):
        book_to_del = await self.get_a_book(book_uid=book_uid, session=session)
        if book_to_del is None:
            return None

        await session.delete(book_to_del)
        await session.commit()
        return {
            "message": "Book deleted",
            "book_uid": book_uid,
        }

    #tips:写一个新的服务,通过外键user_uid获取图书
    async def get_user_books(self,user_uid:str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).where(Book.user_uid == user_uid).order_by(desc(Book.published_date))
        result = await session.execute(statement)
        return result.scalars().all()

    #tips:写一个服务,通过输入图书即可知道该图书是谁发布的

bk_service = BookService()
