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
from src.middleware import register_middleware

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

# important:下方均是添加自定义error的异常处理器


# app.add_exception_handler(
#     UserAlreadyExists,
#     handler=create_exception_handler(
#         status_code=status.HTTP_403_FORBIDDEN,
#         initial_detail={
#             'message': 'User with email already exists.',
#             'error_code': 'user_already_exists',
#         }
#     )
#
# )

#
# app.add_exception_handler(
#     InsufficientPermission,
#     handler=create_exception_handler(
#         status_code=status.HTTP_403_FORBIDDEN,
#         initial_detail={
#             'message': 'Insufficient permissions.',
#             'error_code': 'permission_denied',
#             'resolution':'Please provide a valid permission.'
#         }
#     )
#
# )

# tips:为app添加中间件
register_middleware(app)

# tips:由于这样看不够美观且不符合封装的思想,所以将其转移到errors中并定义为register_all_errors函数
register_all_errors(app)

# tips:如果不想遇到Internal Server Error,那么我们也可以定义一个异常处理器
#  但是格式和上方不同,而是类似于在errors.py中定义的异常处理器那样

@app.exception_handler(500)
async def internal_server_errors(request, exc):
    return JSONResponse(
        content={
            'message': 'Oops, something went wrong.',
            'error_code': 'internal_server_errors',
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
