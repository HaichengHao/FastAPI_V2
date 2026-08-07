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
