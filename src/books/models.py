from datetime import datetime,date
from sqlmodel import SQLModel,Field,Column
import sqlalchemy.dialects.postgresql as pg
import uuid

class TimeStampMinxin:
    created_time:datetime=Field(sa_column=Column(pg.TIMESTAMP,default=datetime.now))
    updated_time:datetime=Field(sa_column=Column(pg.TIMESTAMP,default=datetime.now))

class Book(SQLModel,TimeStampMinxin,table=True):
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

    def __repr__(self):
        return f"<Book{self.title}>"
