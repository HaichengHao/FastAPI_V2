from datetime import datetime,date
from typing import Optional,Annotated
import uuid
import re
from pydantic import BaseModel,Field,field_validator
from src.books.models import Book
class PublicUserSchema(BaseModel):
    username:Annotated[str,Field(max_length=8)]
    first_name: str=Field(max_length=25)
    last_name: str=Field(max_length=25)
    email:str

    @field_validator('email')
    def validate_email(cls, value):
        ptn = r'^[A-Za-z0-9_\-\.]+@(163\.com|qq.com|gmail.com)$'
        if re.match(ptn, value):
            return value
        else:
            return '邮箱格式有误,请检查'



class UserSchema(PublicUserSchema):
    uid:uuid.UUID
    is_verified: bool
    password_hash:str=Field(exclude=True)
    created_at: datetime
    updated_at: datetime


class UserCreatedSchema(PublicUserSchema):
    password: Annotated[str, Field(description="最低6字符", min_length=6)]

class RespSchema(PublicUserSchema):
    books:list[Book]

#tips:定义用户登录schema

class UserLoginSchema(BaseModel):
    email:str
    password:str


#tips:创建邮件发送路由要用到的Schema

class EmailSchema(BaseModel):
    email_address:list[str]

