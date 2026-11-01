from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer  # important 必须引入
from fastapi.requests import Request
from fastapi.security.http import HTTPAuthorizationCredentials
from typing import Annotated, Any
from src.db.main import get_session
from src.auth.utils import decode_token
from src.db.redis import token_in_blocklist  # tips:新增用于添加阻塞列表
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.service import user_service
from src.auth.model import User
from src.errors import InvalidCredentials,AccountNotVerified,InvalidToken,AccessTokenRequired,RefreshTokenRequired,InsufficientPermission

# important:HTTPBearer允许我们保护一个端点,并使其仅在有人以持有者加令牌的形式提供其令牌时才能被访问


class TokenBearer(HTTPBearer):
    def __init__(self, auth_error=True):
        super().__init__(auto_error=auth_error)

    async def __call__(self, request: Request):
        creds = await super().__call__(request)  # tips:继承__call__
        token = creds.credentials  # tips: 拿到请求中携带的凭证令牌
        token_data = decode_token(token)  # important:把token解码，拿到载荷数据
        if not self.token_valid(token):
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
            #     'error': 'This token is invalid or has revoked',
            #     'resolution': 'Please get new token'
            # })
            raise InvalidToken()
        # tips:
        '''
        在检查令牌是否有效之后,将继续检查令牌是否在`阻止列表[也就是db.redis.token_in_blocklist]`中,
        这一步将会接收传入的JTI,jti来自于调用utils时候传入的payload中设置的jti,也就是login_service中
        被调用之后返回的jsonresponse中的access_token与refresh_token中'''

        # token_data已经是解码后的token了,那么就可以从中取出

        if await token_in_blocklist(token_data['jti']):
            # tips:如果不为空，则说明阻塞队列中有该jti,说明该jti对应的令牌已经是无效令牌了,所以不能进行授权内的操作,需要重新获取新的token
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
            #     'error': 'This token is invalid or has revoked',
            #     'resolution': 'Please get new token'
            # })
            raise InvalidToken()

        self.verify_token_data(token_data)
        return token_data

    # pass

    def token_valid(self, token: str):
        token_data = decode_token(token)
        # if token_data:
        #     return True
        # else:
        #     return False
        return token_data is not None

    # tips:这里我们定义一个方法用于验证token但是具体实现用子类重写
    def verify_token_data(self, token_data: dict):
        raise NotImplementedError('Please Override this method in child class')


# tips:访问令牌判定
class AccessTokenBearer(TokenBearer):
    # tips:覆盖父类中的verify_token_data
    def verify_token_data(self, token_data: dict):
        if token_data and token_data['refresh']:
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN, detail="Please provide an access token"
            # )
            raise AccessTokenRequired()
        return token_data


access_token_bearer = AccessTokenBearer()


# tips:刷新令牌判定,这个类用于重载父类中的verify_token_data,实现access_token刷新
class RefreshTokenBearer(TokenBearer):
    # tips:覆盖父类中的verify_token_data
    def verify_token_data(self, token_data: dict):
        if token_data and not token_data['refresh']:  # tips:如果不是刷新令牌就返回报错
            # raise HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN, detail="Please provide an refresh token"
            # )
            raise RefreshTokenRequired()
        return token_data


refresh_token_bearer = RefreshTokenBearer()


# ----------基于用户身份进行鉴权分块代码----------------#
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
