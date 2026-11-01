from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.books.schemas import BookCreateSchema, BookSchema, BookUpdateSchema, BookDetailSchema
from src.db.main import get_session

from .service import bk_service
from src.auth.dependencies import access_token_bearer, role_checker

from src.errors import BookNotFound, BookAlreadyExists

book_router = APIRouter(
    tags=["books"]
    , dependencies=[Depends(access_token_bearer), Depends(role_checker)]  # tips:创建路由级依赖,这样访问图书就需要先登录获取token才行
)  # important:新增角色检查器依赖项,作为权限角色检查,


@book_router.get("/", response_model=List[BookDetailSchema], description="Get all books")
async def get_all_books(session: Annotated[AsyncSession, Depends(get_session)]):
    return await bk_service.get_all_books(session)


@book_router.post("/", status_code=status.HTTP_201_CREATED, description="Create a book", response_model=BookSchema)
async def create_a_book(
        book_data: BookCreateSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
        token_details: Annotated[dict, Depends(access_token_bearer)]
) -> BookSchema:
    user_id = token_details['user']['user_uid']  # important:从token中
    new_book = await bk_service.create_books(book_data=book_data, user_uid=user_id, session=session)
    if new_book is None:  # important:书籍重复时候就抛出冲突
        # raise HTTPException(
        #     status_code=status.HTTP_409_CONFLICT,
        #     detail=f"Book {book_data.title} already exists.",
        # )
        raise BookAlreadyExists()
    return new_book


@book_router.get("/{book_uid}", description="Get one book by uid", response_model=BookDetailSchema)
async def get_a_book(book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]) -> BookSchema:
    book = await bk_service.get_a_book(book_uid, session)
    if book:
        return book
    # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    raise BookNotFound()


@book_router.patch("/{book_uid}", description="Update a book", response_model=BookSchema)
async def update_book(
        book_uid: str,
        book_update_data: BookUpdateSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> BookSchema:
    updated_book = await bk_service.update_book(book_uid, book_update_data, session)
    if updated_book:
        return updated_book
    # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    raise BookNotFound()


@book_router.delete("/{book_uid}", description="Delete a book")
async def del_book(book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]) -> dict:
    book_to_delete = await bk_service.delete_book(book_uid, session)
    if book_to_delete:
        return book_to_delete
    # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    raise BookNotFound()


# tips:创建一个新的api端点,用于获取某用户的所有图书
@book_router.get("/user/{user_uid}", response_model=List[BookSchema], description="Get user's all books by user_uid")
async def get_user_books_submissions(uid: str,
                                     session: Annotated[AsyncSession, Depends(get_session)],
                                     token_details: Annotated[dict, Depends(access_token_bearer)]):
    user_uid = token_details['user']['user_uid']  # tips:可以看看dependencies.py中get_current_user的payload结构
    '''
    payload={
    'user':{
        'email': user.email,
        'user_uid':str(user.uid),
    },
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
    'jti': str(user.jti),
    'refresh': str(user.refresh_token),
    },

    '''
    return await bk_service.get_user_books(user_uid, session)
