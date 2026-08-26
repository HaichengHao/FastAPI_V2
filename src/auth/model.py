from datetime import datetime
from typing import Optional, List
import uuid
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import func


class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            default=uuid.uuid4,
            primary_key=True,
            nullable=False
        )
    )
    username: str
    email: str
    first_name: str
    last_name: str
    role: str = Field(
        sa_column=Column(
            pg.VARCHAR,
            nullable=False,
            server_default='user'
        )
    )
    password_hash: str = Field(exclude=True)
    is_verified: bool = Field(default=False)  #tips:默认不授权，因为后期要对接邮件服务

    # ✅ 直接用 Field，不用 sa_column
    created_time: datetime = Field(
        default_factory=datetime.now,
        nullable=False
    )
    updated_time: datetime = Field(
        default_factory=datetime.now,
        nullable=False
    )

    books: List['Book'] = Relationship(
        back_populates='user',
        sa_relationship_kwargs={'lazy': 'selectin'}
    )
    reviews: List['BookReview'] = Relationship(back_populates='user')

    def __repr__(self):
        return f"<User {self.username}>"