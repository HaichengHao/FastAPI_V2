from fastapi import HTTPException, status
from fastapi.security import HTTPBearer  # important 必须引入
from fastapi.requests import Request
from fastapi.security.http import HTTPAuthorizationCredentials
from src.auth.utils import decode_token
from src.db.redis import token_in_blocklist #tips:新增用于添加阻塞列表


# important:HTTPBearer允许我们保护一个端点,并使其仅在有人以持有者加令牌的形式提供其令牌时才能被访问


class TokenBearer(HTTPBearer):
    def __init__(self, auth_error=True):
        super().__init__(auto_error=auth_error)

    async def __call__(self, request: Request):
        creds = await super().__call__(request)  # tips:继承__call__
        token = creds.credentials  # tips: 拿到请求中携带的凭证令牌
        token_data = decode_token(token)  # important:把token解码，拿到载荷数据
        if not self.token_valid(token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
                'error': 'This token is invalid or has revoked',
                'resolution': 'Please get new token'
            })

        #tips:
        '''
        在检查令牌是否有效之后,将继续检查令牌是否在`阻止列表[也就是db.redis.token_in_blocklist]`中,
        这一步将会接收传入的JTI,jti来自于调用utils时候传入的payload中设置的jti,也就是login_service中
        被调用之后返回的jsonresponse中的access_token与refresh_token中'''

        # token_data已经是解码后的token了,那么就可以从中取出

        if await token_in_blocklist(token_data['jti']):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
                'error': 'This token is invalid or has revoked',
                'resolution': 'Please get new token'
            })

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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Please provide an access token"
            )
        return token_data


access_token_bearer = AccessTokenBearer()


# tips:刷新令牌判定,这个类用于重载父类中的verify_token_data,实现access_token刷新
class RefreshTokenBearer(TokenBearer):
    # tips:覆盖父类中的verify_token_data
    def verify_token_data(self, token_data: dict):
        if token_data and not token_data['refresh']:  # tips:如果不是刷新令牌就返回报错
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Please provide an refresh token"
            )
        return token_data


refresh_token_bearer = RefreshTokenBearer()
