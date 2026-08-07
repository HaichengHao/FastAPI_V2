from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.books.schemas import BookCreateSchema, BookSchema, BookUpdateSchema
from src.db.main import get_session

from .service import bk_service
from src.auth.dependencies import access_token_bearer


book_router = APIRouter(
    tags=["books"]
    , dependencies=[Depends(access_token_bearer)] #tips:创建路由级依赖,这样访问图书就需要先登录获取token才行
)


@book_router.get("/", response_model=List[BookSchema], description="Get all books")
async def get_all_books(session: Annotated[AsyncSession, Depends(get_session)]):
    return await bk_service.get_all_books(session)


@book_router.post("/", status_code=status.HTTP_201_CREATED, description="Create a book", response_model=BookSchema)
async def create_a_book(
        book_data: BookCreateSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> BookSchema:
    new_book = await bk_service.create_books(book_data, session)
    if new_book is None:  # important:书籍重复时候就抛出冲突
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book {book_data.title} already exists.",
        )
    return new_book


@book_router.get("/{book_uid}", description="Get one book by uid", response_model=BookSchema)
async def get_a_book(book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]) -> BookSchema:
    book = await bk_service.get_a_book(book_uid, session)
    if book:
        return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")


@book_router.patch("/{book_uid}", description="Update a book", response_model=BookSchema)
async def update_book(
        book_uid: str,
        book_update_data: BookUpdateSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> BookSchema:
    updated_book = await bk_service.update_book(book_uid, book_update_data, session)
    if updated_book:
        return updated_book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")


@book_router.delete("/{book_uid}", description="Delete a book")
async def del_book(book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]) -> dict:
    book_to_delete = await bk_service.delete_book(book_uid, session)
    if book_to_delete:
        return book_to_delete
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
