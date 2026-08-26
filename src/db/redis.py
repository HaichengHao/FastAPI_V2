'''
整体思路:
创建阻塞列表,也就是过期不可用的token对应的JTI
这样默认的token是有效的，而在redis中存储的是已经失效的在阻塞列表中的token

'''
from redis.asyncio import Redis

from src.config import project_settings


JTI_EXPIRY = 3600

token_blocklist = Redis(
    host=project_settings.REDIS_HOST,
    port=project_settings.REDIS_PORT,
    db=0,
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
