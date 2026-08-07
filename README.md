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


### 用redis来控制令牌刷新
```shell
uv add aioredis 
```

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
```python

```
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



