from datetime import date, datetime
from typing import Optional
import uuid

from pydantic import BaseModel


class BookSchema(BaseModel):
    uid: uuid.UUID
    title: str
    author: str
    publisher: str
    published_date: date  #tips:注意要和model对照
    page_count: int
    language: str
    created_time: datetime
    updated_time: datetime


class BookCreateSchema(BaseModel):
    title: str
    author: str
    publisher: str
    published_date: date
    page_count: int
    language: str


class BookUpdateSchema(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[date] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
