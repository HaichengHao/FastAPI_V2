from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
import uuid
from sqlalchemy import func

if TYPE_CHECKING:
    from src.auth.model import User


class Book(SQLModel, table=True):
    __tablename__ = "books"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4,
        )
    )
    title: str
    author: str
    publisher: str
    published_date: date
    page_count: int
    language: str

    # 直接定义时间字段
    created_time: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP,
            server_default=func.now(),
            nullable=False
        )
    )
    updated_time: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP,
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )

    user_uid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    user: Optional['User'] = Relationship(back_populates='books')
    reviews: List['BookReview'] = Relationship(back_populates='book')

    #tips:给书籍加上标签字段
    # book_tag:list['BookTag'] = Relationship(back_populates='book')

    def __repr__(self):
        return f"<Book {self.title}>"


class BookReview(SQLModel, table=True):
    __tablename__ = "book_reviews"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4,
        )
    )
    book_uid: Optional[uuid.UUID] = Field(default=None, foreign_key="books.uid")
    user_uid: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    review_text: Optional[str] = Field(default=None, nullable=True)
    rating: int = Field(le=5, ge=0, default=None, nullable=True)

    # 直接定义时间字段
    created_time: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP,
            server_default=func.now(),
            nullable=False
        )
    )
    updated_time: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP,
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )

    book: Optional['Book'] = Relationship(back_populates='reviews')
    user: Optional['User'] = Relationship(back_populates='reviews')

    def __repr__(self):
        return f"<BookReview {self.book_uid} by {self.user_uid}>"