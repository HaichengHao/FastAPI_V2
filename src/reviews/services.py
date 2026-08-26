import uuid

from src.books.models import BookReview
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from sqlmodel import desc, select
from typing import Annotated
from fastapi import Depends, HTTPException, status
from src.auth.service import user_service
from src.books.service import bk_service
from src.auth.dependencies import access_token_bearer
from src.reviews.schemas import ReviewCreateSchema


class ReviewService:
    # 定义添加书籍的方法,需要传入用户唯一标识user_uid,所以要从token_details里拿
    # 或者使用用户邮箱也可以，它也是唯一标识
    # 还需要传入书籍的uid,这样就能对应图书了
    async def add_review2book(self,
                              # email:str,
                              user_uid: uuid.UUID,
                              book_uid: uuid.UUID,
                              session: Annotated[AsyncSession, Depends(get_session)],
                              # review_content:str,
                              # rating:int
                              review_data: ReviewCreateSchema
                              ):
        try:
            # 通过book_uid获取目标图书
            book = await bk_service.get_a_book(book_uid=book_uid, session=session)
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Book not found"
                )
            # 通过user_uid获取用户
            user = await user_service.get_user_by_uid(uid=user_uid, session=session)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            #tips:创建评论
            new_review = BookReview(
                **review_data.model_dump()  # tips:解包模式数据给模型,这样BookReview就接收到数据创建review了
            )

            new_review.user = user
            new_review.book = book

            session.add(new_review)
            await session.commit()
            await session.refresh(new_review)

            return new_review

        except HTTPException:
            # 重新抛出已经处理过的 HTTP 异常
            raise

        except Exception as e:
            # 打印真实错误，方便调试
            print(f"Database Error: {e}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    async def get_reviews(self, session: Annotated[AsyncSession, Depends(get_session)]):
        pass


review_service = ReviewService()
