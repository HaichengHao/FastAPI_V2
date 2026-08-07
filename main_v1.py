from fastapi import FastAPI,Query,Header
from typing import Annotated
from pydantic import BaseModel,Field, field_validator
import uvicorn
import re
app=FastAPI()

#------
# 定义请求体
#------

class GreetingBody(BaseModel):
    uname:Annotated[str,Field(alias='username',description='输入用户名')]='小明'
    age:Annotated[int,Field(ge=1,le=100,description='输入年龄')]
    email: str

    # tips:还有一种验证方式,这是文档推荐的官方方式,从pydantic引入field_validator来验证需要的字段
    @field_validator('email')
    def validate_email(cls, value):
        ptn = r'^[A-Za-z0-9_\-\.]+@(163\.com|qq\.com|42du\.cn)$'
        if re.match(ptn, value, re.S):
            return value
        else:
            return '格式有问题,请重新输入'



class BookCreateModel(BaseModel):
    title:str
    author:str

#-----
# 定义路由
#-----
@app.get('/')
async def read_root():
    return {
        'message':'hello world'
    }

@app.get('/greet')
async def greet2u(gbody:GreetingBody):
    return gbody


@app.post('/create_book')
async def create_book(book_data:BookCreateModel):
    return {
        'title':book_data.title,
        'author':book_data.author
    }
    
@app.get('/get_headers',status_code=200)
async def get_headers(
    accept:str|None=Header(None),
    content_type:str = Header(None),
    user_agent:str=Header(None),
    host:str=Header(None)
):
    request_headers={}
    
    request_headers['Accept']=accept
    request_headers['Content-Type']=content_type
    request_headers['user_agent']=user_agent
    request_headers['host']=host
    return request_headers
#tips:这里用uvicorn托管
if __name__ == '__main__':
    uvicorn.run(app=app,host='127.0.0.1',port=8088)