import uuid
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel,Field,Column
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from pydantic import field_validator

class User(SQLModel, table=True):
    __tablename__ = "users"
    uid:uuid.UUID=Field(sa_column=Column(pg.UUID,default=uuid.uuid4,primary_key=True,nullable=False))
    username:str
    email:str
    first_name:str
    last_name:str
    password_hash:str=Field(exclude=True) #tips:指定隐藏
    is_verified: bool = Field(default=False)
    created_time:datetime=Field(sa_column=Column(pg.TIMESTAMP,default=datetime.now))
    updated_time:datetime=Field(sa_column=Column(pg.TIMESTAMP,default=datetime.now))

    def __repr__(self):
        return f"<User {self.username}>"