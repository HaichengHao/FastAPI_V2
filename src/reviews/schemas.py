from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
import uuid


class ReviewSchema(BaseModel):
    uid: uuid.UUID
    book_uid: Optional[uuid.UUID]
    user_uid: Optional[uuid.UUID]
    review_text: Optional[str]
    rating: int=Field(ge=1,le=5)
    created_time: datetime
    updated_time: datetime




class ReviewCreateSchema(BaseModel):
    review_text: Optional[str]
    rating: int=Field(ge=1,le=5)

