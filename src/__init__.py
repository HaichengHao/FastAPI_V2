from fastapi import FastAPI

from src.auth.routers import auth_router
from src.books.routes import book_router
from contextlib import asynccontextmanager
from src.db.main import init_db
from loguru import logger
import time
#important:创建异步上下文管理器


@asynccontextmanager
async def life_span(app: FastAPI):
    start_time = time.time()
    logger.info('服务器正在启动')
    await init_db()
    yield
    db_init_time=time.time()-start_time
    logger.info(f'程序总执行时间{db_init_time}s')
    logger.success('生命周期事件完成')


#tips:生产模式要隐藏
# app = FastAPI(description='书籍管理', docs_url=None, redoc_url=None)

version="V1.0.0"
#important:注意绑定lifespan
app = FastAPI(description='书籍管理',version=version,title='Books API',lifespan=life_span)
app.include_router(book_router,prefix=f"/api/{version}/books",tags=['books'])
app.include_router(auth_router,prefix=f"/api/{version}/auth",tags=['auth'])



