#tips:构建常用工具类，实现密码校验
from datetime import timedelta, datetime
import jwt
from passlib.context import CryptContext
import uuid
from src.config import project_settings
from loguru import logger
from itsdangerous import URLSafeTimedSerializer

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
    payload['user']=user_data #important:指定user键存储用户信息字典
    #tips:设置过期时间，等于从当前时间加上设定的过期时间，如果过期时间没有设置，那就永不过期[不推荐，所以应该换为默认过期时间1小时],
    # payload['exp']=datetime.now() + expires_delta if expires_delta else None
    payload['exp']=datetime.now() + (expires_delta if expires_delta else timedelta(seconds=ACCESS_TOKEN_EXPIRE_MINUTES))

    #tips：设置JWT_ID(jti)
    payload['jti']=str(uuid.uuid4())
    payload['refresh']=refresh

    token=jwt.encode(
        payload=payload, #tips:有效载荷，payload是一个字典
        key=project_settings.JWT_SECRET_KEY,
        algorithm=project_settings.JWT_ALOGRITHM,
        # expires_delta=expires_delta
    ) #tips:encode默认返回的是一个字符串,它的说明都写了Encode the payload as JSON Web Token
        #  也就是加密payload字典为一个jwt
    return token

def decode_token(token:str):
    try:
        token_data=jwt.decode( #tips:传入jwt token，输出payload字典
            jwt=token,
            key=project_settings.JWT_SECRET_KEY,
            algorithms=project_settings.JWT_ALOGRITHM,

        )
        #tips:Verify the jwt token signature and return the token claims
        return token_data
    except jwt.PyJWTError as e:
        logger.exception(e)
        return None



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