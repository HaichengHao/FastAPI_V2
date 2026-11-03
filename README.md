from asyncpg.pgproto.pgproto import timedelta

## 为什么要用sa_?

----
在 SQLModel 中，以 `sa_` 开头的参数都是用来与底层 SQLAlchemy 进行交互的（"sa" 代表 SQLAlchemy）。因为 SQLModel 是 Pydantic（负责数据校验）和 SQLAlchemy（负责数据库操作）的结合体，这些参数允许你绕过 SQLModel 的默认推导，直接对底层数据库列进行高级定制。

以下是你代码中涉及到的几个常见的 `sa_` 参数：

### 1. `sa_column` (SQLAlchemy Column)
**作用**：直接传入一个完整的 SQLAlchemy `Column` 对象，**完全接管**该字段的数据库列定义。
**你的代码场景**：
```python
uid: uuid.UUID = Field(sa_column=Column(pg.UUID, ...))
```
因为 PostgreSQL 的 `UUID` 类型是特定方言的类型，SQLModel 无法自动推导，所以你需要用 `sa_column` 显式告诉它底层数据库应该使用 `pg.UUID` 类型。

**⚠️ 避坑指南**：当你使用了 `sa_column` 时，`Field()` 中其他与数据库列相关的参数（如 `primary_key`, `nullable`, `default` 等）都会被**忽略**。所有的列属性都必须写在 `Column()` 里面。

### 2. `sa_column_kwargs` (SQLAlchemy Column Keyword Arguments)
**作用**：向底层的 SQLAlchemy `Column` 构造函数传递额外的关键字参数字典。
**常见场景**：通常用于设置自动更新时间戳。
```python
updated_time: datetime = Field(
    default_factory=datetime.now, 
    sa_column_kwargs={"onupdate": datetime.now}  # 记录更新时自动刷新时间
)
```
*注：如果你需要同时使用 `sa_column` 和 `onupdate`，可以直接写在 `Column` 里：`Column(pg.TIMESTAMP, default=datetime.now, onupdate=datetime.now)`。*

### 3. `sa_type` (SQLAlchemy Type)
**作用**：仅覆盖底层的 SQLAlchemy 数据类型，但不像 `sa_column` 那样完全接管整个列的定义。
**常见场景**：指定字符串长度、JSON 类型等。
```python
name: str = Field(sa_type=String(32))
```

---

### 💡 针对你当前代码的优化建议

在你的 `TimeStampMinxin` 中，你使用了 `sa_column=Column(pg.TIMESTAMP, default=datetime.now)`。

**这里有一个隐藏的问题**：`datetime.now` 如果直接作为 `default` 传入 SQLAlchemy，它会在**模块加载时**执行一次，导致所有插入的数据都使用同一个时间。

**正确的动态生成时间写法**：
建议使用 SQLModel 原生的 `default_factory` 配合 `sa_column_kwargs`，这样既安全又能触发 Pydantic 的校验：

```python
class TimeStampMixin:
    created_time: datetime = Field(
        default_factory=datetime.now, 
        sa_column=Column(pg.TIMESTAMP)
    )
    updated_time: datetime = Field(
        default_factory=datetime.now, 
        sa_column=Column(pg.TIMESTAMP, onupdate=datetime.now)  # 更新时自动刷新
    )
```

**总结**：
- 需要改**整个列**（如指定特殊的 PG 类型、外键）：用 `sa_column`
- 只需要改**数据类型**（如 String 长度）：用 `sa_type`
- 只需要加**附加属性**（如 onupdate、comment）：用 `sa_column_kwargs`

---


# 关于Alembic的新用法

### 以前是这么用的
```shell
alembic init alembic 
```
这样可以在项目根目录创建一个叫alembic的文件，但是这样是同步的


### 在这次的v2版本中学到的新用法
```shell
alembic init -t async migration
```
- `-t`可以指定模板
- async 表示使用的是异步模板创建
- 至于后面这个migration是自己指定的,就像上面的alembic一样会生成一个数据库版本控制文件

### 接下来差不多还是和之前的一样

修改alembic.ini的`sqlalchemy.url`
```python   
# database URL.  This is consumed by the user-maintained env.py script only.
# other means of configuring database URLs may be customized within the env.py
# file.
#sqlalchemy.url = driver://user:pass@localhost/dbname


sqlalchemy.url = postgresql+asyncpg://postgres:qwerty@127.0.0.1:5432/my_db


```
> 其实这里解决了我之前的一个疑惑，我之前（在原来的FastAPI学习中）用alembic同步的时候用的是异步的
> `postgresql+asyncpg`,然后我同步的时候用了支持同步的driver`postgresql+psycopg2`
> 这次使用了异步模板，所以应该不用那么麻烦了么?

还有就是修改migrations文件夹下的`env.py`将需要进行控制的表进行导入

```python
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

from src.books.models import Book
from src.auth.model import User

target_metadata=[Book.metadata,User.metadata]


#或者,是不是也可以像之前SQLAlchemy那种写法似的用SQLModel来作为直接引入呢?
#因为之前我直接用SQLAlchemy来作深度定制表,且它们都继承自DeclaritiveBase的子类Base
#所以可以把繁琐的表引入直接写成类引入，既from src.models import Base
# target_metadata=[Base.metadata]
from sqlmodel import SQLModel
target_metadata=[SQLModel.metadata]
```
---

### 或者，我们可以用新的玩法!!

既，只用修改env.py
因为env.py留有操作alembic.ini配置的config,我们可以用`config
```python 
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

#important:导入我们的模型并指定我们的目标数据库】
from src.auth.model import User
from src.books.models import Book
from sqlmodel import SQLModel
from src.config import project_settings

#important:下面这个设置的是对alembic.ini的访问,
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.

database_url=project_settings.DATABASE_URL
config = context.config
#tips:使用set_main_option来设置alembic.ini文件中的sqlalchemy的值
config.set_main_option("sqlalchemy.url",database_url )
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None


target_metadata=SQLModel.metadata

```
### 然后还要修改script.py.mako
```
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel   ✔️✔️✔️✔️✔️导入哦！！
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade schema."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade schema."""
    ${downgrades if downgrades else "pass"}
```

-----
### 之后就是进行合并

```shell
alembic revision --autogenerate -m "提交信息(自己写)"
alembic upgrade head
```

```shell
(FastAPI_V2) PS D:\FastAPI_V2> alembic revision --autogenerate -m "init"
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.schemas
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.tables
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.types
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.constraints
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.defaults
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.comments
INFO  [alembic.autogenerate.compare.tables] Detected added table 'users'
INFO  [alembic.autogenerate.compare.tables] Detected removed table 'company'
Generating D:\FastAPI_V2\migrations\versions\f56bf1880088_init.py ...  done
(FastAPI_V2) PS D:\FastAPI_V2> alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> f56bf1880088, init
```

-----

# JWT认证

jwt三大部分组成
- headers
- payload 载荷，要携带的数据
- verified_signature 认证签名

> 在env文件中配置JWT_SECRET_KEY和JWT_ALOGRITHM,config中引入即可
- config.py
```python
from pydantic_settings import BaseSettings,SettingsConfigDict


class MYSettings(BaseSettings):
    DATABASE_URL:str
    JWT_SECRET_KEY:str
    JWT_ALOGRITHM:str
    model_config=SettingsConfigDict(
        env_file='.env',
        extra='ignore'
    )


project_settings = MYSettings()

```

### 生成的话可以用python脚本随机生成一个
```shell
(FastAPI_V2) PS D:\FastAPI_V2> python
Python 3.12.13 (main, May 10 2026, 19:35:37) [MSC v.1944 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import secrets
>>> secrets.token_hex(16)
'f684615811611497d28089e2ec803xxx'
```

### 在utils中实现JWT
- auth/utils.py
```python
#tips:构建常用工具类，实现密码校验
from datetime import timedelta, datetime
import jwt
from passlib.context import CryptContext
import uuid
from src.config import project_settings
from loguru import logger

passwd_context = CryptContext(
    schemes=["bcrypt"]
)


#tips:生成密码哈希
def generate_password_hash(password: str):
    return passwd_context.hash(password)

#tips:构建密码校验服务
def verify_password(plain_password, hashed_password):
    return passwd_context.verify(plain_password, hashed_password)


'''
jwt三大部分组成
headers
payload 载荷，要携带的数据
verified_signature 认证签名
'''
ACCESS_TOKEN_EXPIRE_MINUTES = 3600
def create_access_token(user_data:dict, expires_delta:timedelta = None,refresh:bool = False):
    payload = {} #创建一个空字典用来放有效载荷
    payload['user']=user_data
    #tips:设置过期时间，等于从当前时间加上设定的过期时间，如果过期时间没有设置，那就永不过期[不推荐，所以应该换为默认过期时间1小时],
    # payload['exp']=datetime.now() + expires_delta if expires_delta else None
    payload['exp']=datetime.now() + (expires_delta if expires_delta else timedelta(seconds=ACCESS_TOKEN_EXPIRE_MINUTES))

    #tips：设置JWT_ID(jti)
    payload['jti']=str(uuid.uuid4())
    payload['refresh']=refresh

    token=jwt.encode(
        payload=payload, #tips:有效载荷
        key=project_settings.JWT_SECRET_KEY,
        algorithm=project_settings.JWT_ALOGRITHM,
        # expires_delta=expires_delta
    )
    return token

def decode_token(token:str):
    try:
        token_data=jwt.decode(
            jwt=token,
            key=project_settings.JWT_SECRET_KEY,
            algorithms=project_settings.JWT_ALGORITHM,

        )
        return token_data
    except jwt.PyJWTError as e:
        logger.exception(e)
        return None

```

### 然后是service中构建JWT认证回路
- auth/service.py
```python
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette import status

from src.auth.utils import generate_password_hash,verify_password
from src.auth.model import User
from src.auth.schemas import UserSchema, UserLoginSchema
from sqlmodel import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import get_session
from src.auth.utils import create_access_token,decode_token


class UserService:
    async def create_user(self, user_data: UserSchema, session: Annotated[AsyncSession, Depends(get_session)]):
        user_exist = await self.get_user_by_email(user_data.email, session)
        if user_exist:
            return None  # tips:如果用户存在，返回空值给路由，让路由处理下一步
        else:
            user_data_dict=user_data.model_dump()
            new_user = User(
                **user_data_dict
            )
            #tips:数据库中存储的是加密后的密码，是密文
            new_user.password_hash=generate_password_hash(user_data_dict['password'])
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

    async def get_user_by_uid(self, uid: str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(User).where(User.uid == uid)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(User).where(User.email == email)
        target_user = await session.execute(statement)
        return target_user.scalar_one_or_none()  # tips:如果有就返回，没有就返回none

    async def dele_user_by_uid(self, email: str, session: Annotated[AsyncSession, Depends(get_session)]):
        user_to_del = await self.get_user_by_email(email, session)

        if user_to_del:  # tips:如果返回不为空,则表示确实查到了要删除的用户
            await session.delete(user_to_del)
            await session.commit()
            return {
                'message': 'User deleted',
            }
        else:  # tips:如果没查到该用户id表示该用户不存在，所以无法删除
            return None

    async def mofy_user(self, email: str, update_data: UserSchema,
                        session: Annotated[AsyncSession, Depends(get_session)]):
        user_exist = await self.get_user_by_email(email, session)
        if user_exist:
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(user_exist, field, value)



    #tips:定义登录校验服务
    async def login_service(self,login_data:UserLoginSchema,session:Annotated[AsyncSession,Depends(get_session)]):
        email=login_data.email
        password = login_data.password
        user = await self.get_user_by_email(email, session)
        if user:
            password_valid=verify_password(plain_password=password,hashed_password=user.password_hash)
            #tips:如果用户存在,那就进行密码的校验
            if password_valid: #tips:数据库查验通过则进行下一步操作
                #tips:如果用户存在，那么就进入下一步jwt操作,为该用户创建访问令牌和刷新令牌
                access_token=create_access_token(
                    user_data={
                        'email': user.email,
                        'user_uid':str(user.uid),
                    },

                )

                #tips:创建刷新令牌
                refresh_token=create_access_token(
                    user_data={
                        'email': user.email,
                        'user_uid':str(user.uid),
                    },
                    refresh=True,
                    expires_delta=timedelta(days=2),
                )

                return JSONResponse(
                    content={
                        "message": "Successfully logged in",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user":{
                            "email": user.email,
                            "uid": str(user.uid),
                        }
                    }
                )
            else:
                return {
                    'message': '密码有误，请检查后重新输入',
                    'email': user.email, #tips:传入这个是方便前端处理的时候不用再输一遍邮箱了
                }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="该用户不存在，请先创建"
            )
user_service = UserService()
```


### 定义路由函数使用JWT

```python
#tips:定义jwt认证路由
@auth_router.post('/login')
async def login_user(login_data: UserLoginSchema,session: Annotated[AsyncSession, Depends(get_session)]):
    result = await user_service.login_service(login_data, session=session)
    return result
```


### 创建auth的Bearer依赖,以便引用
```python
from fastapi.security import HTTPBearer



#important:HTTPBearer允许我们保护一个端点,并使其仅在有人以持有者加令牌的形式提供其令牌时才能被访问


class AccessTokenBearer(HTTPBearer):
    pass

access_token_bearer = AccessTokenBearer()

```

### 我们用让Authorization保护book的路由
```python
from src.auth.dependencies import access_token_bearer


book_router = APIRouter(
    tags=["books"]
    , dependencies=[Depends(access_token_bearer)] #tips:创建路由级依赖,这样访问图书就需要先登录获取token才行
)

```
> 这样使用书籍路由时都需要提供access_token,我们登录的时候返回有access_token,所以访问书籍路由的时候要填入Headers
> 并设置Headers的`Authorization`为 Bearer加上登录成功后返回的access_token

![](imgs/Snipaste_2026-07-26_10-11-30.png)

>这只是最基本的方式,这只是一个演示，其实令牌并没有受到保护，所以接下来要重写一下dependenncies.py

```python
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer #important 必须引入
from fastapi.requests import Request
from fastapi.security.http import HTTPAuthorizationCredentials
from src.auth.utils import decode_token


# important:HTTPBearer允许我们保护一个端点,并使其仅在有人以持有者加令牌的形式提供其令牌时才能被访问


class TokenBearer(HTTPBearer):
    def __init__(self, auth_error=True):
        super().__init__(auto_error=auth_error)

    async def __call__(self, request: Request):
        creds = await super().__call__(request)  #tips:继承__call__
        token = creds.credentials #tips: 拿到请求中携带的凭证令牌
        token_data = decode_token(token) #important:把token解码，拿到载荷数据
        if not self.token_valid(token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

        self.verify_token_data(token_data)
        return token_data

    # pass

    def token_valid(self, token: str):
        token_data = decode_token(token)
        if token_data:
            return True
        else:
            return False

    #tips:这里我们定义一个方法用于验证token但是具体实现用子类重写
    def verify_token_data(self, token_data: dict):
        raise NotImplementedError('Please Override this method in child class')

#tips:访问令牌判定
class AccessTokenBearer(TokenBearer):
    #tips:覆盖父类中的verify_token_data
    def verify_token_data(self, token_data: dict):
        if token_data and token_data['refresh']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Please provide an access token"
            )
        return token_data


access_token_bearer = AccessTokenBearer()

#tips:刷新令牌判定,这个类用于重载父类中的verify_token_data,实现access_token刷新
class RefreshTokenBearer(TokenBearer):
    # tips:覆盖父类中的verify_token_data
    def verify_token_data(self, token_data: dict):
        if token_data and not token_data['refresh']: #tips:如果不是刷新令牌就返回报错
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Please provide an refresh token"
            )
        return token_data


refresh_token_bearer = RefreshTokenBearer()

```
刷新令牌的路由
```python
@auth_router.post('/refresh_token')
async def refresh_token(token_details:Annotated[dict,Depends(refresh_token_bearer)]):
    expiry_timestamp=token_details['exp'] #tips:拿到解码token_data中的payload['exp']
    print(expiry_timestamp)
    #important:利用fromtimestamp将时间戳转换为日期时间对象
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now(): #tips:如果过期时间大于当前时间,那么就创建一个新的访问令牌
        new_access_token=create_access_token(
            user_data=token_details['user'],
        )
        return JSONResponse(
            content={
                "access_token": new_access_token,
            }
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or Expired token")

```

### 令牌刷新流程
![](./imgs/tkg.svg)

----
### 利用redis来实现令牌回收

- 导入包
```shell
uv add aioredis
```
- 配置.env和config
```text
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```
> 利用redis存储jti的方式，不存储原始token防止泄露,
> 实现思路是，维持阻塞列表而非通过列表，
> 既默认都是可用的，但是如果用户退出，那么就在阻塞列表添加已经退出用户的令牌的JTI

- db/redis.py
构建redis客户端,实现阻塞用户的添加
```python
from aioredis import StrictRedis  #tips:StrictRedis和Redis差不多
from src.config import project_settings

# token_blocklist=Redis() 用这个其实也可以
JTI_EXPIRY=3600
#tips:其实就是创建了一个redis_client
token_blocklist=StrictRedis(
    host=project_settings.REDIS_HOST,
    port=project_settings.REDIS_PORT,
    db=0
)

'''
整体思路:
创建阻塞列表,也就是过期不可用的token对应的JTI
这样默认的token是有效的，而在redis中存储的是已经失效的在阻塞列表中的token

'''

#tips:定义一个函数添加jti到redis中
'''
我们并不直接把jwttoken存储进redis
而是存储每条jwt_token对应的jti(JwTId)
'''
async def add_jti_to_blocklist(jti:str)->None:
    await token_blocklist.set(
        name=jti,
        value="",
        ex=JTI_EXPIRY

    )

    '''
    其实就是调用redis设置了一个set,名称为jti,然后过期时间也设置一下'''

async def token_in_blocklist(jti:str)->bool:
    jti = await token_blocklist.get(jti)
    '''
    从redis中查询，看看有没有jti,如果有说明JTI对应的令牌已经失效了'''
    return jti is not None

```
- auth/dependencies.py
> 修改dependencies的token_data验证逻辑  
> 在检查令牌是否有效之后,将继续检查令牌是否在`阻止列表[也就是db.redis.token_in_blocklist]`中,  
> 这一步将会接收传入的JTI,jti来自于调用utils时候传入的payload中设置的jti,也就是login_service中  
> 被调用之后返回的jsonresponse中的access_token与refresh_token中  

- auth/routers.py

```python
@auth_router.get('/logout')
async def revoke_token(token_details:Annotated[dict,Depends(access_token_bearer)]):
    jti=token_details['jti']

    #tips:拿到了jti之后把它加在阻止列表中
    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={
            "message": "Logged out successfully",#tips:返回成功注销
        },
        status_code=status.HTTP_200_OK
    )

```

### 令牌吊销逻辑
![](./imgs/token_bearer.svg)

---

## 基于用户身份进行授权
- 开始之前:

要在model中添加可以用于角色区分的字段role,所以要修改数据库字段并进行更新

- auth/model.py
```python
import uuid
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from pydantic import field_validator


class User(SQLModel, table=True):
    __tablename__ = "users"
    uid: uuid.UUID = Field(sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True, nullable=False))
    username: str
    email: str
    first_name: str
    last_name: str
    role: str = Field(  # tips:创建角色字段
        sa_column=Column(
            pg.VARCHAR, nullable=False, server_default='user'
        )
    )
    password_hash: str = Field(exclude=True)  # tips:指定隐藏
    is_verified: bool = Field(default=False)
    created_time: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_time: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"<User {self.username}>"

```
只要对字段进行了修改,那就必须要进行提交
```python
alembic revision --autogenerate -m "add role"
alembic upgrade head
```


---
利用依赖项获取到token数据后拿到用户的邮箱进行数据库查询  
并将查询到的用户对象返回


定义角色检查器,实现用户角色校验

- auth/dependencies.py
```python
# tips:获取当前用户
# important:对令牌的任何检查都将由这个依赖项完成
#  使用了依赖注入,想要查询到当前用户必须传入令牌
async def get_current_user(token_details: Annotated[dict, Depends(access_token_bearer)],
                           session: Annotated[AsyncSession, Depends(get_session)]):
    user_email = token_details['user']['email']  # tips:拿出token中payload的user键下的字典中的email
    '''
    payload={
    'user':{
        'email': user.email,
        'user_uid':str(user.uid),
    },
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
    'jti': str(user.jti),
    'refresh': str(user.refresh_token),
    },
    
    '''
    user = await user_service.get_user_by_email(user_email, session)
    return user

# tips:定义角色检查器
class RoleChecker:

    # ----------基于用户身份进行鉴权分块代码----------------#
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self,current_user:Annotated[User,Depends(get_current_user)])->Any:
        if current_user.role in self.allowed_roles:
            return True
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="YOU ARE NOT ALLOW TO PERFORM THIS ACTION")


#tips:实例化角色检查器
role_checker = RoleChecker(
    ['user','admin']
)
```

- auth/routers.py
```python
@auth_router.get('/me')
async def get_now_user(user: Annotated[dict, Depends(get_current_user)],
                          _:Annotated[bool, Depends(role_checker)]): #important:使用占位符号,表示不关心变量,而是必须执行依赖项目,检查角色
    # async def get_now_user(user=Depends(get_current_user),_:bool=Depends(role_checker)):
    return user


```


有了role_checker之后,可以在需要进行角色检查的路由上使用它作为依赖项,对角色进行检查,实现角色控制


-----

### 模型(model)与模式(schema)关系

#### 一对多

> 这样一个场景:用户能够提交图书,并且这些由他们提交的图书能够追溯回他们本人,
> 具体做法是可以在图书表上建立一个外键,将外键关联到用户的UID
> 可以回忆一下之前sqlalchemy所学的外键位置判断,一个用户可以发布多个图书,那么就要在图书表放置外键约束
> 

在books的model中设置外键约束,指定的外键为users表的uid
- books/models.py

```python
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
    #tips:设置外键约束
    user_uid:Optional[uuid.UUID]=Field(default=None,foreign_key="users.uid") #tips:引用的是users表的uid

```

> 还是那样的准则,一旦动了数据模型结构,那就要alembic迁移同步更新
```shell
(FastAPI_V2) PS D:\FastAPI_V2> alembic revision --autogenerate -m "relate users to books"
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.schemas
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.tables
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.types
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.constraints
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.defaults
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.comments
INFO  [alembic.autogenerate.compare.tables] Detected added column 'books.user_uid'
INFO  [alembic.autogenerate.compare.constraints] Detected added foreign key (user_uid)(uid) on table books
Generating D:\FastAPI_V2\migrations\versions\d03dc4724c63_relate_users_to_books.py ...  done
(FastAPI_V2) PS D:\FastAPI_V2> alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 1f0e67cd8bcc -> d03dc4724c63, relate users to books
```

然后修改创建图书的服务,以及需要改写路由


- book/service.py
```python
    async def create_books(self, book_data: BookCreateSchema,user_uid:str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).where(Book.title == book_data.title)
        result = await session.execute(statement)
        book_exist = result.scalar_one_or_none()
        if book_exist:
            return None

        new_book = Book(**book_data.model_dump())
        new_book.user_uid=user_uid  #important:增加这个,让发布图书的信息携带用户的user_uid
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book) #important:提交之后要记得刷新
        return new_book

```

引入token_details(虽然已经引入路由级别的了,但是这里我们需要定制路径级别的,所以引入方便拿到token数据中携带的用户的user_uid)
- book/routes.py

```python
@book_router.post("/", status_code=status.HTTP_201_CREATED, description="Create a book", response_model=BookSchema)
async def create_a_book(
        book_data: BookCreateSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
        token_details:Annotated[dict, Depends(access_token_bearer)]
) -> BookSchema:
    user_id=token_details['user']['user_uid'] #important:从token中
    new_book = await bk_service.create_books(book_data=book_data,user_uid=user_id,session=session)
    if new_book is None:  # important:书籍重复时候就抛出冲突
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book {book_data.title} already exists.",
        )
    return new_book

```

接下来编写根据用户user_uid获取图书的服务和路由
- books/service.py

```python
    #tips:写一个新的服务,通过外键user_uid获取图书
    async def get_user_books(self,user_uid:str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).where(Book.user_uid == user_uid).order_by(desc(Book.published_date))
        result = await session.execute(statement)
        return result.scalars().all()

```

- books/routes.py
```python
#tips:创建一个新的api端点,用于获取某用户的所有图书
@book_router.get("/user/{user_uid}", response_model=List[BookSchema], description="Get user's all books by user_uid")
async def get_user_books_submissions(uid:str,
                                     session: Annotated[AsyncSession, Depends(get_session)],
                                     token_details:Annotated[dict, Depends(access_token_bearer)]):
    user_uid = token_details['user']['user_uid'] #tips:可以看看dependencies.py中get_current_user的payload结构
    '''
    payload={
    'user':{
        'email': user.email,
        'user_uid':str(user.uid),
    },
    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
    'jti': str(user.jti),
    'refresh': str(user.refresh_token),
    },

    '''
    return await bk_service.get_user_books(user_uid,session)


```
![](./imgs/sbsbooks.svg)

---

但是这样的方式还不够完美,回想一下现在其实只是用了外键约束而已,还没有上关系(relationship)  
回忆一下之前sqlalchemy那版fastapi学习路程,除了创建外键,也可以设置back_ref(flask)/back_populates(fastapi_sqlalchemy)

- books/models.py
```python
from datetime import datetime,date
from typing import Optional
# from src.auth.model import User  写这就会遇到大坑!!!
from sqlmodel import SQLModel,Field,Column,Relationship
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
    #tips:设置外键约束
    user_uid:Optional[uuid.UUID]=Field(default=None,foreign_key="users.uid") #tips:引用的是users表的uid
    user:Optional['User']=Relationship(back_populates='books')
    #important:back_populates = "books" 这不是胡乱写的,因为在users表中也实现了关系books字段,不要把它跟表名混淆，
    # back_populates各自指向的是在其它表中本表字段名
    # ,也就是说现在users表可以通过books来访问了,
    # 可以在图书端使用books.user即可得知该图书是谁发布的
    #
    def __repr__(self):
        return f"<Book{self.title}>"

```

- auth/model.py
> **注意**:由于sqlmodel使用懒加载,但在某些情况下(尤其是使用异步数据库API时)可能会出现问题  
> 所以要设置`sa_relationship_kwargs={'lazy':'selectin'}`来避免这个问题,具体可以查阅sqlmodel的官方文档
```python
import uuid
from datetime import datetime
from typing import Optional
# from src.books.models import Book   写这就会遇到大坑!!!
import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from pydantic import field_validator


class User(SQLModel, table=True):
    __tablename__ = "users"
    uid: uuid.UUID = Field(sa_column=Column(pg.UUID, default=uuid.uuid4, primary_key=True, nullable=False))
    username: str
    email: str
    first_name: str
    last_name: str
    role: str = Field(  # tips:创建角色字段
        sa_column=Column(
            pg.VARCHAR, nullable=False, server_default='user'
        )
    )
    password_hash: str = Field(exclude=True)  # tips:指定隐藏
    is_verified: bool = Field(default=False)
    created_time: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_time: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    books:list['Book']=Relationship(back_populates='user',sa_relationship_kwargs={'lazy':'selectin'}) #tips:设置关系,在用户端访问users.books即可访问到books表

    def __repr__(self):
        return f"<User {self.username}>"


```
**一定要注意对应关系**
```python
#auth/model.py
books:list['Book']=Relationship(back_populates='user',sa_relationship_kwargs={'lazy':'selectin'}) #tips:设置关系,在用户端访问users.books即可访问到books表
#books/models.py
user:Optional['User']=Relationship(back_populates='books')

```


之后还需要修改auth/schemas.py
在响应模式(RespSchema)中加入books
- auth/schemas.py
```python
from src.books.models import Book
class RespSchema(PublicUserSchema):
    books:list[Book]
```

之后修改获取当前用户信息的路由  
设置返回模型为RespSchema,这样也会一并把该用户发布的图书也显示出来

- auth/routers
```python
# tips:获取当前用户
@auth_router.get('/me',response_model=RespSchema)
async def get_now_user(user: Annotated[dict, Depends(get_current_user)],
                          _:Annotated[bool, Depends(role_checker)]): #important:使用占位符号,表示不关心变量,而是必须执行依赖项目,检查角色
    # async def get_now_user(user=Depends(get_current_user),_:bool=Depends(role_checker)):
    return user

```
![](./imgs/getme.png)
---

### 遇到了大坑
原来没有注意到这点,之前的fastapi_learn中做这种relationship的时候就是不需要在自身文件再次导入model的!!!!!
所以去掉互相导入
```shell
WARNING:  StatReload detected changes in 'src\auth\model.py'. Reloading...
 Process SpawnProcess-2:
Traceback (most recent call last):
  File "C:\Users\20201\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\Lib\multiprocessing\process.py", line 314, in _bootstrap
    self.run()
  File "C:\Users\20201\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\Lib\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
  File "D:\FastAPI_V2\.venv\Lib\site-packages\uvicorn\_subprocess.py", line 80, in subprocess_started
    target(sockets=sockets)
  File "D:\FastAPI_V2\.venv\Lib\site-packages\uvicorn\server.py", line 74, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\20201\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "C:\Users\20201\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\20201\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\Lib\asyncio\base_events.py", line 691, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "D:\FastAPI_V2\.venv\Lib\site-packages\uvicorn\server.py", line 78, in serve
    await self._serve(sockets)
  File "D:\FastAPI_V2\.venv\Lib\site-packages\uvicorn\server.py", line 85, in _serve
    config.load()
  File "D:\FastAPI_V2\.venv\Lib\site-packages\uvicorn\config.py", line 493, in load
    self.loaded_app = self.load_app()
                      ^^^^^^^^^^^^^^^
  File "D:\FastAPI_V2\.venv\Lib\site-packages\uvicorn\config.py", line 427, in load_app
    return import_from_string(self.app)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\FastAPI_V2\.venv\Lib\site-packages\uvicorn\importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\20201\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\Lib\importlib\__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 999, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "D:\FastAPI_V2\main.py", line 2, in <module>
    from src import app
  File "D:\FastAPI_V2\src\__init__.py", line 3, in <module>
    from src.auth.routers import auth_router
  File "D:\FastAPI_V2\src\auth\routers.py", line 7, in <module>
    from src.auth.schemas import UserCreatedSchema, UserLoginSchema, RespSchema
  File "D:\FastAPI_V2\src\auth\schemas.py", line 6, in <module>
    from src.books.models import Book
  File "D:\FastAPI_V2\src\books\models.py", line 3, in <module>
    from src.auth.model import User
  File "D:\FastAPI_V2\src\auth\model.py", line 4, in <module>
    from src.books.models import Book
ImportError: cannot import name 'Book' from partially initialized module 'src.books.models' (most likely due to a circular import) (D:\FastAPI_V2\src\books\models.py) 
```
你遇到的这个报错，本质上是代码中的“死循环”——也就是经典的循环导入（Circular Import）问题。

🚨 错误原因分析

根据报错信息，你的代码依赖关系形成了一个闭环：
src/auth/model.py 尝试导入 Book (来自 src.books.models)。
src/books/models.py 尝试导入 User (来自 src.auth.model)。

当 Python 试图加载其中一个文件时，发现需要先加载另一个，而另一个又回头依赖第一个，导致模块未初始化完成就被再次调用，从而引发 ImportError。

💡 解决方案

在 FastAPI (SQLAlchemy) 项目中，解决这种循环依赖最标准、最优雅的方法是使用字符串引用来定义关系，而不是直接导入类。

方法一：使用字符串定义关系（推荐）

在 SQLAlchemy 的 relationship 中，你可以直接写类名的字符串，而不需要实际导入那个类。

修改 src/auth/model.py：

from sqlalchemy import Column, Integer, String
from src.database import Base
❌ 删除这行导入：from src.books.models import Book

class User(Base):
    tablename = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    
    # ✅ 修改这里：使用字符串 "Book" 代替类对象 Book
    # 如果是一对多关系（一个用户有多本书）：
    books = relationship("Book", back_populates="owner") 

修改 src/books/models.py：

from sqlalchemy import Column, Integer, String, ForeignKey
from src.database import Base
❌ 删除这行导入：from src.auth.model import User

class Book(Base):
    tablename = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # ✅ 修改这里：使用字符串 "User" 代替类对象 User
    owner = relationship("User", back_populates="books")

原理： SQLAlchemy 会在内部处理这个字符串，等到所有模型都加载完毕后，再去解析 relationship，从而打破了导入时的死循环。

方法二：延迟导入（不推荐，但在某些逻辑层必须用）

如果你不是在定义 relationship，而是在某个函数内部需要使用对方的类，可以将导入语句移动到函数内部。

src/auth/model.py

class User(Base):
    # ... 字段定义 ...

    def get_books_count(self):
        # ✅ 仅在函数内部导入
        from src.books.models import Book 
        return len(self.books)

📌 总结

请检查你的 src/auth/model.py 和 src/books/models.py，删除文件顶部的相互导入语句，并将 relationship() 中的参数改为类名的字符串形式（例如 "Book" 和 "User"）。

修改后保存，FastAPI 的热重载应该就能正常启动了。

----


## 复杂关联关系

### 书籍评论

一个用户可以为多本书籍撰写评论，一个书籍也可以有多个评论  
所以关联关系是 
用户(1)->评论(多)    
书籍(1)->评论(多)    

对于公共模块，不想陷入循环导入的问题,就需要把它放在一个都可以访问到的合适位置,不然就会像上面一样踩了大坑


在books/models.py中设置bookReview模型
- books/models.py
```python
#tips:设置书籍评论模型
class BookReview(SQLModel,TimeStampMinxin,table=True):
    __tablename__ = "book_reviews"
    book_uid:Optional[uuid.UUID]=Field(default=None,foreign_key="books.uid")
    user_uid:Optional[uuid.UUID]=Field(default=None,foreign_key="users.uid")
    review_text:Optional[str]=Field(default=None,nullable=True)
    rating:int=Field(lt=5,gt=0,default=None,nullable=True) #tips:书籍评分
    
    def __repr__(self):
        return f"<BookReview{self.book_uid} by {self.user_uid}>"
```
**然后记得alembic revision --autogenerate -m 'xxx'并且alembic upgrade head**
```shell
(FastAPI_V2) PS D:\FastAPI_V2> alembic revision --autogenerate -m "add review table"
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.schemas
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.tables
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.types
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.constraints
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.defaults
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.comments
INFO  [alembic.autogenerate.compare.tables] Detected added table 'book_reviews'
INFO  [alembic.autogenerate.compare.constraints] Detected NOT NULL on column 'books.created_time'
INFO  [alembic.autogenerate.compare.constraints] Detected NOT NULL on column 'books.updated_time'
INFO  [alembic.autogenerate.compare.constraints] Detected NOT NULL on column 'users.created_time'
INFO  [alembic.autogenerate.compare.constraints] Detected NOT NULL on column 'users.updated_time'
Generating D:\FastAPI_V2\migrations\versions\4208b7d8b021_add_review_table.py ...  done
(FastAPI_V2) PS D:\FastAPI_V2> alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade d03dc4724c63 -> 4208b7d8b021, add review table
```

### 注意
值得关注的是,本次改动发现了很多之前的问题,model重写了  
还要加上users表和books表与reivews表的关联关系
- auth/model.py
```python
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
    is_verified: bool = Field(default=False)

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
```
- books/models.py
```python
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
```

接下来是创建模式文件,以便实现添加评论时要传入的数据模式
- src/reviews/schemas.py
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
import uuid


class ReviewSchema(BaseModel):
    uid: uuid.UUID
    book_uid: Optional[uuid.UUID]
    user_uid: Optional[uuid.UUID]
    review_text: Optional[str]
    rating: int=Field(le=5)
    created_time: datetime
    updated_time: datetime




class ReviewCreateSchema(BaseModel):
    review_text: Optional[str]
    rating: int=Field(ge=1,le=5)
```

然后是写服务类

- src/reviews/services.py
```python
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

```

然后是路由
- reviews/routes.py
```python
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


```
如果想获取图书中带出它的评论的话，那就需要修改books的schemas了,因为原来的是没加上评论的
- books/schemas.py 
```python
from datetime import date, datetime
from typing import Optional, List
import uuid
from src.reviews.schemas import ReviewSchema
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
    ·
    ·
    ·
    ·
class BookDetailSchema(BookSchema):
    reviews: List[ReviewSchema]
```
书籍路由的返回模型改成BookDetailSchema
把获取一个图书和获取多个图书都改为BookDetailSchema
- books/routes.py
```python
@book_router.get("/", response_model=List[BookDetailSchema], description="Get all books")
async def get_all_books(session: Annotated[AsyncSession, Depends(get_session)]):
    return await bk_service.get_all_books(session)

@book_router.get("/{book_uid}", description="Get one book by uid", response_model=BookDetailSchema)
async def get_a_book(book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]) -> BookSchema:
    book = await bk_service.get_a_book(book_uid, session)
    if book:
        return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")


```
然后尝试访问http://127.0.0.1:8088/api/V1.0.0/books获取全部图书带评论

![](/imgs/reviewdemo.png)
#### 这里遇到了懒加载的问题,关键是利用selectinload来解决书籍详情无法加载出其对应的评论的问题

- books/services.py
```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import desc, select

from src.books.models import Book
from src.books.schemas import BookCreateSchema, BookUpdateSchema
from src.db.main import get_session


class BookService:
    async def get_all_books(self, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).options(selectinload(Book.reviews)).order_by(desc(Book.published_date)) #important:解决懒加载导致的问题
        result = await session.execute(statement)
        return result.scalars().all() #tips:用scalars来拿到数据行

    async def get_a_book(self, book_uid: str, session: Annotated[AsyncSession, Depends(get_session)]):
        statement = select(Book).options(selectinload(Book.reviews)).where(Book.uid == book_uid)
        result = await session.execute(statement)
        return result.scalar_one_or_none() #tips:用scalar_one_or_none()来检验数据库中是否真的有图书
```

----

## 自定义api异常

将在该文件实现异常类，当应用程序中发生错误时候就抛出这些异常类
有些错误是通用的，比如“not_find"的那些错误，以及每次出错时都会遇到的"内部服务器错误"
也可能存在由于用户操作权限不够产生的错误


- src/errors.py
```python
from typing import Any, Callable
from fastapi.requests import Request
from fastapi.responses import JSONResponse
class BooklyException(Exception):
    """
    this is the base exception class for all other exceptions
    """
    pass
class InvalidToken(BooklyException):
    """User has provided an invalid token"""
    pass

class RevokedToken(BooklyException):
    """User has provided a revoked token"""
    pass
class AccessTokenRequired(BooklyException):
    """User has provided a refresh token when an access token is required"""
    pass
class RefreshTokenRequired(BooklyException):
    """User has provided an access token when an access token is required"""
    pass

class UserAlreadyExists(BooklyException):
    """User has provided an email for a user who already exists"""
    pass

class InsufficientPermission(BooklyException):
    """User does not have the necessary permissions to perform an action"""
    pass

class BookNotFound(BooklyException):
    """Book not found exception"""
    pass


class UserNotFound(BooklyException):
    """User not found exception"""
    pass

class InvalidCredentials(BooklyException):
    """Invalid credentials exception"""
    pass

class BookAlreadyExists(BooklyException):
    """Book already exists exception"""
    pass


async def create_exception_handler(status_code:int,initial_detail:Any) -> Callable[[Request,Exception],JSONResponse]:
    async def exception_handler(request:Request,exc:BooklyException):
        return JSONResponse(
            content=initial_detail,
            status_code=status_code,
        )
    return exception_handler
```

然后就是在src/__init__.py中添加异常处理
fastapi为我们提供了这样的方法  
除此之外我们还将单独实现内部500错误的异常处理  

- src/__init__.py
```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette import status

from src.auth.routers import auth_router
from src.books.routes import book_router
from src.reviews.routes import review_router
from src.booktag.routes import booktag_router
from contextlib import asynccontextmanager
from src.db.main import init_db
from src.errors import *
from loguru import logger
import time


# important:创建异步上下文管理器


@asynccontextmanager
async def life_span(app: FastAPI):
    start_time = time.time()
    logger.info('服务器正在启动')
    await init_db()
    yield
    db_init_time = time.time() - start_time
    logger.info(f'程序总执行时间{db_init_time}s')
    logger.success('生命周期事件完成')


# tips:生产模式要隐藏
# app = FastAPI(description='书籍管理', docs_url=None, redoc_url=None)

version = "V1.0.0"
# important:注意绑定lifespan,但是因为life_sapn里塞入了await init_db,所以只在首次数据库初始化时用life_span,之后将其注释掉!!!!!!!
app = FastAPI(description='书籍管理',
              version=version,
              title='Books API',
              # lifespan=life_span
              )
app.include_router(book_router, prefix=f"/api/{version}/books", tags=['books'])
app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=['auth'])

app.include_router(review_router, prefix=f"/api/{version}/review", tags=['review'])

# app.include_router(booktag_router,prefix=f'/api/{version}/booktag',tags=['booktag'])

#important:下方均是添加自定义error的异常处理器




app.add_exception_handler(
    UserAlreadyExists,
    handler=create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={
            'message': 'User with email already exists.',
            'error_code': 'user_already_exists',
        }
    )

)

app.add_exception_handler(
    BookNotFound,
    handler=create_exception_handler(
        status_code=status.HTTP_404_NOT_FOUND,
        initial_detail={
            'message': 'Book not found.',
            'error_code': 'book_not_found',
        }
    )

)

app.add_exception_handler(
    BookAlreadyExists,
    handler=create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={
            'message': 'User already exists.',
            'error_code': 'user_already_exists',
            'resolution':'Please provide a valid user.'
        }
    )

)
app.add_exception_handler(
    UserNotFound,
    handler=create_exception_handler(
        status_code=status.HTTP_404_NOT_FOUND,
        initial_detail={
            'message': 'User not found.',
            'error_code': 'user_not_found',
            'resolution':'Please provide a valid user.'
        }
    )

)


app.add_exception_handler(
    InvalidCredentials,
    handler=create_exception_handler(
        status_code=status.HTTP_400_BAD_REQUEST,
        initial_detail={
            'message': 'Invalid credentials.',
            'error_code': 'invalid_credentials',


        }
    )

)

app.add_exception_handler(
    InvalidToken,
    handler=create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={
            'message': 'Token is invalid.',
            'error_code': 'invalid_token',
            'resolution':'Please get new token'
        }
    )

)

app.add_exception_handler(
    RevokedToken,
    handler=create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        initial_detail={
            'message': 'Token is invalid or has been revoked.',
            'error_code': 'token_revoked',
            'resolution':'Please get new token'
        }
    )

)

app.add_exception_handler(
    AccessTokenRequired,
    handler=create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={
            'message':'Please provide a valid access token.',
            'error_code':'access_token_required',
            'resolution':'Please get new access token'
        }
    )

)

app.add_exception_handler(
    RefreshTokenRequired,
    handler=create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={
            'message':'Please provide a valid refresh token.',
            'error_code':'refresh_token_required',
            'resolution':'Please get new refresh token'
        }
    )

)

app.add_exception_handler(
    InsufficientPermission,
    handler=create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={
            'message': 'Insufficient permissions.',
            'error_code': 'permission_denied',
            'resolution':'Please provide a valid permission.'
        }
    )

)

#tips:如果不想遇到Internal Server Error,那么我们也可以定义一个异常处理器
#  但是格式和上方不同,而是类似于在errors.py中定义的异常处理器那样

@app.exception_handler(500)
async def internal_server_errors(request,exc):
    return JSONResponse(
        content={
            'message': 'Oops, something went wrong.',
            'error_code': 'internal_server_errors',
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
```

除此之外还需要把之前路由或是服务中做的raise通通换成自己定义的异常处理


之后为了方便,将其转移到errors中实现一个register_all_errors(app)  
然后__init__.py在app定义之后调用它`register_all_errors(app)`

```python
def register_all_errors(app:FastAPI):
    app.add_exception_handler(
        UserAlreadyExists,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                'message': 'User with email already exists.',
                'error_code': 'user_already_exists',
            }
        )

    )

    app.add_exception_handler(
        BookNotFound,
        handler=create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                'message': 'Book not found.',
                'error_code': 'book_not_found',
            }
        )

    )
    ·
    ·
    ·
```

----

### 中间件
- 跨域中间件CORSMiddleware
- 受信任主机中间件 TrustedHostMiddleware 
- 自定义日志中间件
- 自定义授权头检查中间件

创建日志记录中间件以及授权头检查中间件(先不用)和跨域中间件以及受信任主机中间件, 
采用现代日志管理loguru
- src/middleware.py
```python
import sys
import time
import logging
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response
from loguru import logger
from fastapi.responses import JSONResponse
from starlette import status

# 1. 清除 loguru 默认的控制台处理器
logger.remove()

# 2. 添加现代化的控制台输出（带颜色高亮）
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
)

# 3. 添加文件输出（按天轮转，保留7天，自动压缩，开启异步队列）
logger.add(
    "app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    compression="zip",
    level="INFO",
    enqueue=True,  # 关键：在 FastAPI 中必须开启，避免阻塞主协程
)


# ============================================================================
# 4. 核心：拦截并接管 Uvicorn 的原生日志
# ============================================================================
# 为什么要写这个类？
# 因为 FastAPI 底层的 Uvicorn 服务器，以及 Python 自带的很多库，
# 都是使用 Python 标准的 `logging` 模块来打印日志的。
# 如果我们不拦截它们，控制台里就会出现两种完全不同风格的日志：
# 一种是 loguru 风格，一种是原生 logging 风格，非常混乱。
# 这个类的作用，就是做一个“翻译官”，把原生 logging 的日志全部转交给 loguru。

class InterceptHandler(logging.Handler):
    """
    自定义的日志处理器：继承自 Python 标准的 logging.Handler。
    当 Python 原生 logging 产生日志时，会调用这个类的 emit 方法。
    """

    def emit(self, record):
        # --- 步骤 1：转换日志级别 ---
        # 原生 logging 的级别是数字（如 INFO=20, ERROR=40），
        # 而 loguru 需要字符串级别的名称（如 "INFO", "ERROR"）。
        try:
            # 尝试将原生日志的级别名称（如 'INFO'）转换为 loguru 认识的级别
            level = logger.level(record.levelname).name
        except ValueError:
            # 如果 loguru 不认识这个级别（比如某些奇怪的自定义级别），
            # 就退而求其次，直接使用原生的数字级别
            level = record.levelno

        # --- 步骤 2：计算真实的代码调用位置（深度） ---
        # 为什么要算深度？
        # 如果不算，loguru 打印出来的日志会显示是在 `InterceptHandler.emit` 这一行
        # 打印的，这毫无意义。我们想知道的是：**到底是哪一行业务代码触发了这条日志**。

        # 获取当前的调用栈帧（frame），初始深度设为 2
        # (0 是 currentframe() 本身，1 是 emit 方法，2 是调用 emit 的地方)
        frame, depth = logging.currentframe(), 2

        # 向上遍历调用栈，跳过 Python 内部 logging 模块的代码
        # 只要当前帧的文件名还是 logging 模块的内部文件，就继续往上找
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # 获取上一层调用者的代码帧
            depth += 1  # 深度加 1

        # --- 步骤 3：将日志转交给 loguru ---
        # logger.opt() 允许我们对 loguru 进行高级配置：
        # - depth=depth: 告诉 loguru 真实的业务代码在第几层，
        #   这样 loguru 就能在日志里正确显示业务代码的文件名和行号。
        # - exception=record.exc_info: 如果这条日志带有异常堆栈信息，
        #   就把它原封不动地传给 loguru，保证异常信息完整打印。
        logger.opt(depth=depth, exception=record.exc_info).log(
            level,  # 转换后的日志级别
            record.getMessage()  # 获取原生日志的纯文本消息内容
        )


# ============================================================================
# 5. 强制接管 Python 全局的 logging 配置
# ============================================================================
# logging.basicConfig() 用于配置全局的日志行为：
# - handlers=[InterceptHandler()]: 把我们刚才写的“翻译官”设置为唯一的日志处理器。
#   这意味着所有原生 logging 的日志都会流经这个处理器。
# - level=0: 设置为最低级别（NOTSET），意思是“不要过滤任何级别的日志”。
#   把所有级别的日志都放行，交给 loguru 去决定哪些该打印、哪些该丢弃。
# - force=True: 强制覆盖之前可能已经存在的 logging 配置。
#   如果不加这个，如果 Uvicorn 提前配置过 logging，我们的拦截可能会失效。
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


# ============================================================================
# 6. FastAPI 中间件注册
# ============================================================================
def register_middleware(app: FastAPI) -> FastAPI:
    # 跨域中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    #important:设置受信任主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        
    )

    # 自定义日志中间件
    @app.middleware('http')
    async def custom_logging(request: Request, call_next):
        # 为当前请求生成唯一 ID，方便全链路追踪
        request_id = str(uuid4())

        start_time = time.time()

        # 使用 contextualize 将 request_id 绑定到当前请求的日志上下文中
        with logger.contextualize(request_id=request_id):
            logger.info(f"业务来了,准备处理 | {request.method} {request.url}")

            # 针对根路径的特殊处理
            if request.url.path == '/':
                return Response(content="欢迎访问")

            # 传递请求给下一个中间件或路由
            response = await call_next(request)

            processing_time = time.time() - start_time
            logger.info(
                f"处理完毕 | 耗时: {processing_time:.4f}s | 状态码: {response.status_code}"
            )

        return response

    # # tips:自定义授权检查中间件
    # # important:值得注意的是，使用中间件时，无法在中间件内部追踪HTTP异常，它会被抛出异常但不会作为响应返回
    # #   所以如果想要响应,那就用JSONResponse
    # @app.middleware("http")
    # async def authorization(request: Request, call_next):
    #     # tips:如果请求的headers中没有授权头Authorization,那就抛出未授权异常
    #     if not 'Authorization' in request.headers:
    #         return JSONResponse(
    #             content={
    #                 "message": "Not Authorized",
    #                 "resolution": "Please provide the right credentials to proceed"
    #             },
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #         )
    #     response = await call_next(request)
    #     return response

```


-----

## 通过电子邮件验证用户账户

- auth/model.py 
在之前的用户数据模型中我设置了一个字段默认为False表示默认用户未授权  
这样做了邮件服务之后就可以通过设置这个字段来表示是否授权
```python
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

```

### 设置mtp服务

- src/mail.py
```python
from fastapi_mail import FastMail,ConnectionConfig,MessageSchema,MessageType
from src.config import project_settings
from pathlib import Path
from fastapi import UploadFile

BASE_DIR = Path(__file__).resolve().parent

#step 1:想要配置 FastMail实例,需要准备链接配置
mail_config = ConnectionConfig(
    MAIL_USERNAME=project_settings.MAIL_USERNAME,
    MAIL_PASSWORD=project_settings.MAIL_PASSWORD,
    MAIL_SERVER=project_settings.MAIL_SERVER,
    MAIL_PORT=project_settings.MAIL_PORT,
    MAIL_FROM=project_settings.MAIL_FROM,
    MAIL_STARTTLS=project_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=project_settings.MAIL_SSL_TLS,
    MAIL_FROM_NAME=project_settings.MAIL_FROM_NAME,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(BASE_DIR,'templates').resolve(), #tips:如果想用HTML模板的电子邮件就需要这个
)

#step 2:连接配置准备好之后就用FastMail将连接配置传入进去
mail_server = FastMail(
    config=mail_config,
) #创建一个FastMail实例
#可以看到要求传入的是ConnectionConfig格式
'''
    
    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config
'''

#step 3: 创建能返回MessageSchema的方法
def create_message(
        recipient_list: list[str], #tips:收件人列表
        subject: str, #tips:邮件主题
        body: str, #tips:正文
        # attachments: UploadFile, #tips:附件
):
    message = MessageSchema(
        recipients=recipient_list,
        subject=subject,
        body=body,
        # attachments=attachments
        subtype=MessageType.html #tips:指定文件类型

    )
    return message

#important:重要的是去auth/router中修改路由

#step 4:发送一封电子邮件测试
# mail_server.send_message(
# 
# )
# 

# 可以看要求传入的是MessageSchema格式
'''
 async def send_message(
        self,
        message: Union[MessageSchema, list[MessageSchema]],
        template_name: Optional[str] = None,
        html_template: Optional[str] = None,
        plain_template: Optional[str] = None,
    ) -> None:'''

```

此外还需要修改auth/schemas.py,补充邮件发送路由用的Schema
- auth/schemas.py
```python
#tips:创建邮件发送路由要用到的Schema

class EmailSchema(BaseModel):
    email_address:list[str]  
    
    注意,前端要传入的话格式应该是
    {
        email_address:['xxxx@qq.com','xxxx@163.com']
    }

```

编写发送路由测试
- auth/routers.py
```python
@auth_router.post('/send_mail')
async def send_mail(emails: EmailSchema):
    emails = emails.email_address
    mailbody = """
        <html>
            <body>
                你好,这是测试!!
            </body>
        </html>
    """

    message = create_message(recipient_list=emails, subject='test mail', body=mailbody)
    await mail_server.send_message(message)
    return {
        'message': 'success send mail',
    }

```


注意要修改config.py以及env文件
- src/config.py
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class MYSettings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALOGRITHM: str
    REDIS_HOST: str="localhost"
    REDIS_PORT: int=65522
    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore'
    )


    #tips:下面是邮件服务所需
    MAIL_USERNAME:str
    MAIL_PASSWORD:str
    MAIL_SERVER:str
    MAIL_PORT:int
    MAIL_FROM:str
    MAIL_STARTTLS:bool
    MAIL_SSL_TLS:bool
    MAIL_FROM_NAME:str
    USE_CREDENTIALS:bool
    VALIDATE_CERTS:bool

project_settings = MYSettings()

```

**注意.env中设置的要和config中的相互对应，不要有不同名的情况!!**  
**MAIL_PORT=465 测了465行，587不行，如果开了465，就把`MAIL_SSL_TLS=True`
如果587行就把`MAIL_SSL_TLS=False`,然后`MAIL_STARTTLS=True`**

```text
MAIL_FROM=xxx@qq.com
MAIL_USERNAME=xxx@qq.com
上面俩的值一样的↑


MAIL_PASSWORD=16位授权码
MAIL_SERVER=smtp.qq.com
#MAIL_PORT=587
MAIL_PORT=465 测了465行，587不行，如果开了465，就把MAIL_SSL_TLS=True
如果587行就把MAIL_SSL_TLS=False,然后MAIL_STARTTLS=True

MAIL_STARTTLS=False
#MAIL_SSL_TLS=False
MAIL_SSL_TLS=True
MAIL_FROM_NAME=NIKOFOX_fastapiV2
USE_CREDENTIALS=True
VALIDATE_CERTS=True
```

![](./imgs/img.png)
----



## 高级服务之群发信息保护

`fastapi-mail` 的设计逻辑比较巧妙：**`recipients` 字段实际上充当了 `To`（收件人）的角色**。

要实现群发且彼此不可见，核心就是：**让 `recipients` 为空，把真实用户列表全部放到 `bcc` 里。**

### 修改方案：将用户列表放入 `bcc`

由于 `recipients` 是必填参数，我们可以给它一个占位邮箱（比如发件人自己），然后把真实用户放入 `bcc`。

修改你的 `create_message` 方法如下：

```python
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType, NameEmail
# ... 其他导入 ...

# 1. 修改 create_message，增加 bcc 参数
def create_message(
        bcc_list: list[str],  # 接收真实的群发用户列表
        subject: str, 
        body: str, 
):
    # 使用一个占位邮箱作为 recipients，防止报错
    placeholder = ["youmail@xx.com"]
    
    message = MessageSchema(
        recipients=placeholder,   # 必须传入一个列表
        bcc=bcc_list,             # 把真实的收件人全部放在这里
        subject=subject,
        body=body,
        subtype=MessageType.html
    )
    return message

# 2. 修改路由中的调用
@auth_router.post('/send_mail')
async def send_mail(emails: EmailSchema):
    emails_addr = emails.email_address  # 真实用户列表
    
    # 将用户列表传给 bcc_list
    message = create_message(
        bcc_list=emails_addr, 
        subject='test mail', 
        body=mailbody
    )
    
    await mail_server.send_message(message)
    return {'message': 'success send mail'}
```

### 效果说明

- **对于真实用户**：他们收到邮件时，**“收件人 (To)” 一栏显示的是“你的发件人邮箱”（即占位邮箱）**，而 `bcc` 里的所有其他真实用户，**他们互相看不到，也看不到发件人自己**。
- **对于你的发件箱**：你发件箱里看到的收件人也是那个占位邮箱，看不到被 `bcc` 出去的真实用户。

这样既满足了 `recipients` 必填的要求，又完美实现了群发隐私保护。

![](./imgs/demo2.png)
![](./imgs/demo1.png)

------




## 邮件认证服务

需要准备一个包
`uv add itsdangerous`

修改utils文件,引入`URLSafeTimedSerializer`(URL安全定时序列化器)，它将帮助我们接收一个字符串，然后将其转换为令牌  
还可以设置时间，以检查该令牌或数据被签名后经过的时间 

- auth/utils.py
```python
from itsdangerous import URLSafeTimedSerializer

# 利用itsdangerous设置令牌，将用户信息进行令牌生成

serializer = URLSafeTimedSerializer(
        secret_key=project_settings.JWT_SECRET_KEY,
        salt="emial-configuration" #tips:加盐,可以自己决定，不要太简单，也可以生成一串hash
    )
def create_url_safe_token(data:dict):
    # serializer = URLSafeTimedSerializer(
    #     secret_key=project_settings.SECRET_KEY,
    #     salt="emial-configuration" #tips:加盐,可以自己决定，不要太简单，也可以生成一串hash
    # )

    token = serializer.dumps(data) #tips:没错，它也可以加盐
    #tips:dumps方法允许我们获取一个值,然后将其序列化为一个对象,或基本上是一个类似于令牌的字符串,就像我们创建的JWT一样
    return token

def decode_url_safe_token(token:str):
    try:
        token_data = serializer.loads(token) #tips:将返回解码后存储在我们令牌内的数据

        return token_data
    except Exception as e:
        logger.exception(e)
```

- auth/service.py

```python
    # #定义更新用户，这里和邮件认证服务有关的！原来上面已经写过了
    async def update_user(self,user:UserSchema,user_data:dict,session:Annotated[AsyncSession,Depends(get_session)]):
        user_exist = await self.get_user_by_email(user.email, session)
        if user_exist:
            for k,v in user_data.items():
                setattr(user_exist, k, v)
            # 提交数据库事务
            await session.commit()

            # 刷新ORM对象，获取数据库最新数据
            await session.refresh(user_exist)

            return user_exist
            
        else:
            raise UserNotFound()
```

- auth/routers.py

  

  signup路由也需要改造,定义注册逻辑链，并使用之前构造好的mail_server来发送验证邮箱如果用户收到验证邮箱的邮件后，点击链接，就会建立起get请求直接跳转到验证链接，这时候就操作更新服务来将用户的标签位`is_verified`修改为True,表示用户认证成功!

```python
# tips:定义注册路由
@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)  # 由于做了邮件改造，所以这里不再返回new_user,自然不能用RespSchema了,不然是会报错的
async def create_user_Account(
        user_data: UserCreatedSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
        request: Request,
):
    email = user_data.email
    # tips:先查一下看看该用户有没有被注册
    result = await user_service.get_user_by_email(email, session=session)
    if result:  # TIPS:如果结果不为空，说明用户已经存在了
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email already registered")
    else:  # 如果不为空那就开始注册逻辑链
        # 调用创建服务创建用户
        new_user = await user_service.create_user(user_data, session=session)

        # 生成safetoken
        token = create_url_safe_token(
            {
                'email': email,

            }
        )
        # ---------
        # 改造,引入通过电子邮件验证用户账户
        # link = f"http://{project_settings.DOMAIN_NAME}/api/v1/auth/verify/{token}"
        link = str(request.url_for('verify_user_account', token=token)) #被静态硬编码坑惨了，所以换动态的，不然老验证不过去
        html_msg = f"""
        <html>
            <body>
                <h1>验证你的电子邮件</h1>
                <p>点此<a href="{link}">链接</a>验证你的邮箱</a></p>
            </body>
        </html>
        """
        # 构建信息，发送给用户
        message = create_message(
            bcc_list=[email],
            subject="Verify your Email",
            body=html_msg

        )

        await mail_server.send_message(message)

        return {
            "message": "Account created successfully! Check email verify your count",
            "user": new_user
        }
        # ---------

        # return new_user


# 创建MPI端点,实现邮箱认证服务
@auth_router.get('/verify/{token}')
async def verify_user_account(token: str, session: Annotated[AsyncSession, Depends(get_session)]):
    # tips:解码收到的token
    token_data =  decode_url_safe_token(token)

    user_email = token_data.get('email')
    if user_email:
        user = await user_service.get_user_by_email(user_email, session=session)
        if not user:
            raise UserNotFound()
        # 如果用户存在，那就调用service来更新用户的信息
        await user_service.update_user(user, {'is_verified': True}, session=session)

        return JSONResponse(
            content={
                "message": "Account verified successfully!!"
            },
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        content={
            "message": "Something went wrong :("
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR

    )




```





### 流程截图

![](./imgs/img_2.png)

![](./imgs/img_3.png)

![](./imgs/img_4.png)

![](./imgs/img_1.png)

然后查看`is_verified`是不是真的变成true了

![](./imgs/img_5.png)

这样就行了!

### 逻辑

![](./imgs/email_verify.svg)







## 密码重置服务

用户需要提供一个邮件地址，取决于链接中是否包含用户的详细信息

- auth/dependencies.py

修改rolechecker的用户验证逻辑,之前我们实现了is_verified默认字段  为false且上面邮件认证服务中设置了is_verified的值的更新路由,那么  接下来就给它串起来,rolechecker要做的加上了检查is_verified是否为  true!!也就是说用户光注册是不行的，还需要点击自己的邮箱链接完成  注册逻辑  

```python
# tips:定义角色检查器
class RoleChecker:

    # ----------基于用户身份进行鉴权分块代码----------------#
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self,current_user:Annotated[User,Depends(get_current_user)])->Any:
        #tips:新增检查,查看用户的数据中is_verified是否为true
        if not current_user.is_verified:
            raise AccountNotVerified()

        if current_user.role in self.allowed_roles:
            return True
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="YOU ARE NOT ALLOW TO PERFORM THIS ACTION")
        raise InsufficientPermission()

#tips:实例化角色检查器
role_checker = RoleChecker(
    ['user','admin']
)

```

- errors.py  

新增未验证异常，也就是说用户只是单纯注册的话是无法登录的，因为设置了rolechecker的is_verified检查

```python
#tips:创建未验证异常
class AccountNotVerified(BooklyException):
    """Account not verified exception"""
    pass

#添加账户未验证异常
app.add_exception_handler(
    AccountNotVerified,
    handler=create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        initial_detail={
            'message': 'Account not verified.',
            'error_code': 'account_not_verified',
            'resolution': 'Please check your email for verification details.'
        }
    )
)

```



---

密码重置的三个步骤

```
1.获取用户的邮箱地址 ->密码重置请求,需要让ta们发送邮箱
2.发送密码重置连接
3.通过post请求提供信息，来重置密码 -> 密码重置确认
```

下面新增服务,实现密码重置服务

- auth/routers.py

```python
@auth_router.post('/pwd-rest-request')
async def pwd_rest(email_data: PasswordResetSchema, session: Annotated[AsyncSession, Depends(get_session)],request:Request):
    email = email_data.email

    if email:
        target_user = await user_service.get_user_by_email(email, session=session)
        if not target_user:
            raise UserNotFound()
        else:
            # 生成safetoken
            token = create_url_safe_token(
                {
                    'email': email,
                }
            )
            # 改造,引入密码重置认证，对应路由在下方实现
            link = str(request.url_for('pwd_reset_confirm', token=token)) #被静态硬编码坑惨了，所以换动态的，不然老验证不过去

            html_msg = f"""
               <html>
                   <body>
                       <h1>重置您的密码</h1>
                       <p>点此<a href="{link}">链接</a>重置密码</a></p>
                   </body>
               </html>
               """
            # 构建信息，发送给用户
            message = create_message(
                bcc_list=[email],
                subject="Verify your Email",
                body=html_msg

            )

            await mail_server.send_message(message)

            return JSONResponse(
                content={
                    "message": "Password reset url have send to your email-box,please check",
                },
                status_code=status.HTTP_200_OK,
            )


# 实现密码重置确认的路由

@auth_router.post('/pwd_rest_confirm/{token}')
async def pwd_reset_confirm(token: str, pwd_data: PasswordConfirmSchema,
                    session: Annotated[AsyncSession, Depends(get_session)]):
    if pwd_data.new_pwd != pwd_data.confirm_new_pwd:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password not match")
    token_data = decode_url_safe_token(token)
    user_email = token_data.get('email')
    if  user_email:
        user = await user_service.get_user_by_email(user_email, session=session)
        if not user:
            raise UserNotFound()
        pwd_hashed = generate_password_hash(pwd_data.confirm_new_pwd)
        await user_service.update_user(user, user_data={'password_hash': pwd_hashed}, session=session)
        return JSONResponse(
            content={
                "message": "Password reset successfully",
            },
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        content={
            "message":"Error occured while trying to reset password",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
```

![](./imgs/img_7.png)

![](./imgs/img_6.png)



使用更新后的密码进行登录

![](./imgs/img_8.png)



-----

# -------------------



## Celery,Redis实现后台任务

利用Celery,Redis对于新的邮件发送任务，将其加入到队列当中实现后台任务

### 方式1，使用fastapi自带的BackgroundTasks

> 将# await mail_server.send_message(message)
> 改造为bg_tasks.add_task(mail_server.send_message,message)

```python
from fastapi import BackgroundTasks


#接下来就是改造原来的需要邮件发送的路由函数
@auth_router.post('/pwd-rest-request')
async def pwd_rest(email_data: PasswordResetSchema, session: Annotated[AsyncSession, Depends(get_session)],request:Request,bg_tasks:BackgroundTasks):
    email = email_data.email

    if email:
        target_user = await user_service.get_user_by_email(email, session=session)
        if not target_user:
            raise UserNotFound()
        else:
            # 生成safetoken
            token = create_url_safe_token(
                {
                    'email': email,
                }
            )
            # 改造,引入密码重置认证，对应路由在下方实现
            link = str(request.url_for('pwd_reset_confirm', token=token)) #被静态硬编码坑惨了，所以换动态的，不然老验证不过去

            html_msg = f"""
               <html>
                   <body>
                       <h1>重置您的密码</h1>
                       <p>点此<a href="{link}">链接</a>重置密码</a></p>
                   </body>
               </html>
               """
            # 构建信息，发送给用户
            message = create_message(
                bcc_list=[email],
                subject="Verify your Email",
                body=html_msg

            )

            # await mail_server.send_message(message)
            bg_tasks.add_task(mail_server.send_message,message) #important:加入到后台任务❗❗❗❗❗就是这里

            return JSONResponse(
                content={
                    "message": "Password reset url have send to your email-box,please check",
                },
                status_code=status.HTTP_200_OK,
            )


```



### 方式2，使用celery

```shell
uv add celery
```

![](./imgs/img_9.png)

使用celery我们可以设置代理，可以用redis或者是rabbitMQ

- src/config.py

> 需要设置结果后端以及broker_url

```python
from celery import Celery
from pydantic_settings import BaseSettings, SettingsConfigDict


class MYSettings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALOGRITHM: str
    REDIS_HOST: str="localhost"
    REDIS_PORT: int=65522
    DOMAIN_NAME:str="127.0.0.1:8088"
    REDIS_URL:str #新增全redis链接方便celery设置
    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore'
    )


    #tips:下面是邮件服务所需
    MAIL_USERNAME:str
    MAIL_PASSWORD:str
    MAIL_SERVER:str
    MAIL_PORT:int
    MAIL_FROM:str
    MAIL_STARTTLS:bool
    MAIL_SSL_TLS:bool
    MAIL_FROM_NAME:str
    USE_CREDENTIALS:bool
    VALIDATE_CERTS:bool

project_settings = MYSettings()

broker_url = project_settings.REDIS_URL  #设置broker_url为redis
result_backend = project_settings.REDIS_URL  #tips:设置结果后端
```

- src/db/redis.py

  把原来的token_blocklist改造为Redis.from_url的方式

```python
'''
整体思路:
创建阻塞列表,也就是过期不可用的token对应的JTI
这样默认的token是有效的，而在redis中存储的是已经失效的在阻塞列表中的token

'''
from redis.asyncio import Redis

from src.config import project_settings


JTI_EXPIRY = 3600

# token_blocklist = Redis(
#     host=project_settings.REDIS_HOST,
#     port=project_settings.REDIS_PORT,
#     db=0,
#     decode_responses=True,
# )
token_blocklist = Redis.from_url(
    project_settings.REDIS_URL,
    decode_responses=True,
)

'''
我们并不直接把jwttoken存储进redis
而是存储每条jwt_token对应的jti(JwTId)
'''
async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(
        name=jti,
        value="",
        ex=JTI_EXPIRY,
    )

'''
    其实就是调用redis设置了一个set,名称为jti,然后过期时间也设置一下'''

async def token_in_blocklist(jti: str) -> bool:
    token_jti = await token_blocklist.get(jti)
    '''
        从redis中查询，看看有没有jti,如果有说明JTI对应的令牌已经失效了'''
    return token_jti is not None

```

如果要在celery任务中运行异步代码，必须想办法将该异步代码转换，或让它在同步代码中运行

推荐使用`asgiref`

asgiref提供了许多函数包装器,但主要是那些帮助将异步代码转换为能在同步代码上下文中运行的包装器，它还提供一个函数包装器，允许在同步代码上下文中运行同步代码

```shell
uv add asgiref
```

- src/celery_tasks

#### 第一个celery任务

> 重点关注原有邮件发送服务的改造，将其功能抽出来做成一个celery任务
>
>  async_to_sync(mail_server.send_message)(message)  既异步服务转为同步服务来实现

```python
from celery import Celery
from src.mail import create_message,mail_server
from asgiref.sync import async_to_sync #使用异步转同步函数
#要创建一个Celery应用，作为celery类的实例

c_app = Celery()

c_app.config_from_object('src.config') #tips:设置celery应用的配置文件的加载位置,我们是在src.config中设置的


#创建第一个任务

@c_app.task()
def send_email(
        u_bcc_list: list[str],
        u_subject:str,
        u_html_msg:str,
):
    message = create_message(
        bcc_list=u_bcc_list, #收件人列表
        subject=u_subject, #主题
        body=u_html_msg #邮件消息内容

    )

    #由于send_message是协程，所以需要将其转换为在同步函数中可以运行的代码才行
    #这时候就需要asgiref的sync方法中的async_to_sync，既异步转同步函数
    # mail_server.send_message(message)  原来的发送方式不再适用

    async_to_sync(mail_server.send_message)(message)
```



- auth/routers.py

改造原来的邮件服务

> 改造为调用send_email.delay()的形式实现同步

```python
from src.celery_tasks import send_email
@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)  # 由于做了邮件改造，所以这里不再返回new_user,自然不能用RespSchema了,不然是会报错的
async def create_user_Account(
        user_data: UserCreatedSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
        request: Request,
        bg_tasks:BackgroundTasks
):
    email = user_data.email
    # tips:先查一下看看该用户有没有被注册
    result = await user_service.get_user_by_email(email, session=session)
    if result:  # TIPS:如果结果不为空，说明用户已经存在了
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email already registered")
    else:  # 如果不为空那就开始注册逻辑链
        # 调用创建服务创建用户
        new_user = await user_service.create_user(user_data, session=session)

        # 生成safetoken
        token = create_url_safe_token(
            {
                'email': email,
            }
        )
        # ---------
        # 改造,引入通过电子邮件验证用户账户
        # link = f"http://{project_settings.DOMAIN_NAME}/api/v1/auth/verify/{token}"
        link = str(request.url_for('verify_user_account', token=token)) #被静态硬编码坑惨了，所以换动态的，不然老验证不过去
        html_msg = f"""
        <html>
            <body>
                <h1>验证你的电子邮件</h1>
                <p>点此<a href="{link}">链接</a>验证你的邮箱</a></p>
            </body>
        </html>
        """
 
        send_email.delay(
            u_bcc_list=[email],
            u_subject="Verify your Email",
            u_html_msg=html_msg

        )

        return {
            "message": "Account created successfully! Check email verify your count",
            "user": new_user
        }

```

同样的，重置密码的路由也是同样思路进行重新设置,不再赘述



### 使用Celery

- uvicorn主进程运行后，新开一个终端

```shell
(FastAPI_V2) PS D:\FastAPI_V2> celery --help
Usage: celery [OPTIONS] [COMMAND] [ARGS]...

  Celery command entrypoint.

Options:
  -A, --app TEXT   #这里就是指定Celery应用所在的模块
  -b, --broker TEXT
  --result-backend TEXT
  --loader TEXT
  --config TEXT
  --workdir PATH
  -C, --no-color
  -q, --quiet
  --version
  --skip-checks          Skip Django core checks on startup. Setting the
                         SKIP_CHECKS environment variable to any non-empty
                         string will have the same effect.
  --help                 Show this message and exit.

Commands:
  amqp     AMQP Administration Shell.
  beat     Start the beat periodic task scheduler.
  call     Call a task by name.
  control  Send the COMMAND control command to the workers.
  events   Event-stream utilities.
  graph    The ``celery graph`` command.
  inspect  Inspect the workers by sending them the COMMAND inspect command.
  list     Get info from broker.
  logtool  The ``celery logtool`` command.
  migrate  Migrate tasks from one broker to another.
  multi    Start multiple worker instances.
  purge    Erase all messages from all known task queues.
  report   Shows information useful to include in bug-reports.
  result   Print the return value for a given task id.
  shell    Start shell session with convenient access to celery symbols.
  status   Show list of workers that are online.
  upgrade  Perform upgrade between versions.
  worker   Start worker instance.
```



- 指定celeryapp,由于我写的在src下的celery_tasks.py里实现的c_app,所以就指定这里就行，如果直接命名就是app,那写路径写成`src.celery_tasks` 就行，且我们需要启动工作者实例,那么后面加上worker

```shell
(FastAPI_V2) PS D:\FastAPI_V2> celery -A src.celery_tasks.c_app worker
```

### 但是！！！大坑，由于我当前开发在win,不是在我的ubuntu，并且celery官方明确说主要支持linux，所以需要换命令

主要解决方法的详细部分已经写到celery坑点.md了

现在换一下命令

```shel
celery -A src.celery_tasks.c_app worker --loglevel=info --pool=solo
```

```shell
(FastAPI_V2) PS D:\FastAPI_V2> celery -A src.celery_tasks.c_app worker --loglevel=info --pool=solo
 
 -------------- celery@aya v5.6.3 (recovery)
--- ***** ----- 
-- ******* ---- Windows-11-10.0.26200-SP0 2026-11-03 11:11:47
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         __main__:0x29876ad9fd0
- ** ---------- .> transport:   redis://127.0.0.1:65522/0
- ** ---------- .> results:     redis://127.0.0.1:65522/0
- *** --- * --- .> concurrency: 18 (solo)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** ----- 
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery
                

[tasks]
  . src.celery_tasks.send_email

[2026-11-03 11:11:47,442: INFO/MainProcess] Connected to redis://127.0.0.1:65522/0
[2026-11-03 11:11:47,450: INFO/MainProcess] mingle: searching for neighbors
[2026-11-03 11:11:48,490: INFO/MainProcess] mingle: all alone
[2026-11-03 11:11:48,531: INFO/MainProcess] celery@aya ready.
```

### 安装celery 图形界面，flower  

```shell
uv add flower
```

- 运行结果后端可视化flower,注意，要有正在运行的worker才能监控

```shell
(FastAPI_V2) PS D:\FastAPI_V2> celery -A src.celery_tasks.c_app flower
2026-11-03 11:39:28.815 | INFO     | logging:callHandlers:1762 - Visit me at http://127.0.0.1:5555
2026-11-03 11:39:28.844 | INFO     | logging:callHandlers:1762 - Broker: redis://127.0.0.1:65522/0
2026-11-03 11:39:28.847 | INFO     | logging:callHandlers:1762 - Registered tasks: 
['celery.accumulate',
 'celery.backend_cleanup',
 'celery.chain',
 'celery.chord',
 'celery.chord_unlock',
 'celery.chunks',
 'celery.group',
 'celery.map',
 'celery.starmap',
 'src.celery_tasks.send_email']
2026-11-03 11:39:28.866 | INFO     | logging:callHandlers:1762 - Connected to redis://127.0.0.1:65522/0
```



![](./imgs/img_10.png)



这时候可以把之前测试邮件发送的服务也改造成celery task

```python
# tips:定义邮件发送路由
@auth_router.post('/send_mail')
async def send_mail(emails: EmailSchema):
    emails_addr = emails.email_address
    mailbody = """
    <html>略
    </html>
    """

    # message = create_message(bcc_list=emails_addr, subject='test mail', body=mailbody)
    # await mail_server.send_message(message)

    #这里也改造

    send_email.delay(
        u_bcc_list=emails_addr,
        u_subject="Test_send",
        u_html_msg=mailbody
    )
    return {
        'message': 'success send mail',
    }

```

值得注意的是,由于u_bcc_list接收的是邮件列表，是list[str]形式的，我最开始搞混了，因为这个测试路由的EmailSchema中的email_address已经是list[str]格式了,所以我最开始写了u_bcc_list=[emails_addr]完全就是错的,是[ ['xxx@qq.com','xxx@163.com'] ]  
这样是错误的,所以去掉外层括号就好了  

再次构造发送邮件请求后成功

![](./imgs/img_12.png)

![](./imgs/img_11.png)

**这里的坑是非常值得注意的，因为会遇到路由没报错但是celery_app报错，因为现在邮件发送的任务已经交给celery task了，所以 
路由触发了就会成功，但是实际邮件到底有没有发送出去还是得看celery task**

