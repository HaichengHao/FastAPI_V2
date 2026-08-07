from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.config import project_settings
from sqlmodel import SQLModel #tips:这里要导入,就像sqlalchemy原生写法中导入Base一样
from src.books.models import Book   #tips:这里要显式导入
from src.auth.model import User #tips:显式导入user表
#tips:创建异步引擎
engine = create_async_engine(
    url=project_settings.DATABASE_URL,
    echo=True
)

#tips:定义初始化数据库方法
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


#tips:创建异步session生成器
async def get_session() -> AsyncSession:
    AsyncSessionlocal=async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with AsyncSessionlocal() as session:
        yield session


