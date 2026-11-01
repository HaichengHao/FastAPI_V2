from datetime import timedelta
from typing import Annotated
from src.errors import UserNotFound,InvalidCredentials
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
            #tips:为用户提供默认角色
            new_user.role="user"
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
            # 提交数据库事务
            await session.commit()

            # 刷新ORM对象，获取数据库最新数据
            await session.refresh(user_exist)

            return user_exist

        else:
            raise UserNotFound()


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
                        'role':user.role
                    },

                )

                #tips:创建刷新令牌
                refresh_token=create_access_token(
                    user_data={
                        'email': user.email,
                        'user_uid':str(user.uid),
                    },
                    refresh=True, #tips:表名其是刷新令牌，如果遇到刷新令牌应当刷新access_token
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
                # return {
                #     'message': '密码有误，请检查后重新输入',
                #     'email': user.email, #tips:传入这个是方便前端处理的时候不用再输一遍邮箱了
                # }
                raise InvalidCredentials()
        else:
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN,
            #     detail="该用户不存在，请先创建"
            # )
            raise UserNotFound()

user_service = UserService()

