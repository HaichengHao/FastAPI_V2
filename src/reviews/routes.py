import uuid

from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from src.auth.dependencies import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.reviews.services import review_service
from src.auth.model import User
from src.auth.dependencies import access_token_bearer,role_checker
from src.auth.dependencies import access_token_bearer, refresh_token_bearer, get_current_user, role_checker
from src.reviews.schemas import ReviewCreateSchema
review_router = APIRouter(
    tags=["review"],
    dependencies=[
        Depends(access_token_bearer),
        Depends(role_checker),
    ]
)


@review_router.post('/book/{book_uid}')
async def add_review2book(
        book_uid: uuid.UUID,
        current_user:Annotated[User,Depends(get_current_user)],
        review_data:ReviewCreateSchema,
        session:Annotated[AsyncSession,Depends(get_session)]
):
    try:
        new_review =await review_service.add_review2book(
            user_uid=current_user.uid,
            book_uid=book_uid,
            session=session,
            # review_content=review_data.review_text,
            # rating=review_data.rating
            review_data=review_data

         )
        return new_review
    except BaseException as e:
        raise HTTPException(status_code=400,detail=f"{e}")
    except HTTPException as e:
        # 如果是业务逻辑抛出的 HTTPException，直接向上抛出
        raise e

