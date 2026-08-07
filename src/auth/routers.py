from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.responses import JSONResponse

from src.auth.schemas import UserSchema, UserCreatedSchema,UserLoginSchema,RespSchema
from src.db.main import get_session
from src.auth.service import user_service
from src.auth.dependencies import access_token_bearer,refresh_token_bearer

from src.auth.utils import create_access_token
from src.db.redis import add_jti_to_blocklist
auth_router = APIRouter(
    tags=['auth']
)


# tips:定义注册路由
@auth_router.post('/signup', response_model=RespSchema, status_code=status.HTTP_201_CREATED)
async def create_user_Account(
        user_data: UserCreatedSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    email = user_data.email
    # tips:先查一下看看该用户有没有被注册
    result = await user_service.get_user_by_email(email, session=session)
    if result:  # TIPS:如果结果不为空，说明用户已经存在了
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email already registered")
    else:
        new_user =  await user_service.create_user(user_data, session=session)
        return new_user

#tips:定义jwt认证路由
@auth_router.post('/login')
async def login_user(login_data: UserLoginSchema,session: Annotated[AsyncSession, Depends(get_session)]):
    result = await user_service.login_service(login_data, session=session)
    return result


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
