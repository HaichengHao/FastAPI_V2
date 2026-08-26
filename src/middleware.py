import sys
import time
import logging
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response
from loguru import logger
from fastapi.responses import JSONResponse
from starlette import status

# 1. 清除 loguru 默认的控制台处理器
logger.remove()

# 2. 添加现代化的控制台输出（带颜色高亮）
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
)

# 3. 添加文件输出（按天轮转，保留7天，自动压缩，开启异步队列）
logger.add(
    "app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    compression="zip",
    level="INFO",
    enqueue=True,  # 关键：在 FastAPI 中必须开启，避免阻塞主协程
)


# ============================================================================
# 4. 核心：拦截并接管 Uvicorn 的原生日志
# ============================================================================
# 为什么要写这个类？
# 因为 FastAPI 底层的 Uvicorn 服务器，以及 Python 自带的很多库，
# 都是使用 Python 标准的 `logging` 模块来打印日志的。
# 如果我们不拦截它们，控制台里就会出现两种完全不同风格的日志：
# 一种是 loguru 风格，一种是原生 logging 风格，非常混乱。
# 这个类的作用，就是做一个“翻译官”，把原生 logging 的日志全部转交给 loguru。

class InterceptHandler(logging.Handler):
    """
    自定义的日志处理器：继承自 Python 标准的 logging.Handler。
    当 Python 原生 logging 产生日志时，会调用这个类的 emit 方法。
    """

    def emit(self, record):
        # --- 步骤 1：转换日志级别 ---
        # 原生 logging 的级别是数字（如 INFO=20, ERROR=40），
        # 而 loguru 需要字符串级别的名称（如 "INFO", "ERROR"）。
        try:
            # 尝试将原生日志的级别名称（如 'INFO'）转换为 loguru 认识的级别
            level = logger.level(record.levelname).name
        except ValueError:
            # 如果 loguru 不认识这个级别（比如某些奇怪的自定义级别），
            # 就退而求其次，直接使用原生的数字级别
            level = record.levelno

        # --- 步骤 2：计算真实的代码调用位置（深度） ---
        # 为什么要算深度？
        # 如果不算，loguru 打印出来的日志会显示是在 `InterceptHandler.emit` 这一行
        # 打印的，这毫无意义。我们想知道的是：**到底是哪一行业务代码触发了这条日志**。

        # 获取当前的调用栈帧（frame），初始深度设为 2
        # (0 是 currentframe() 本身，1 是 emit 方法，2 是调用 emit 的地方)
        frame, depth = logging.currentframe(), 2

        # 向上遍历调用栈，跳过 Python 内部 logging 模块的代码
        # 只要当前帧的文件名还是 logging 模块的内部文件，就继续往上找
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # 获取上一层调用者的代码帧
            depth += 1  # 深度加 1

        # --- 步骤 3：将日志转交给 loguru ---
        # logger.opt() 允许我们对 loguru 进行高级配置：
        # - depth=depth: 告诉 loguru 真实的业务代码在第几层，
        #   这样 loguru 就能在日志里正确显示业务代码的文件名和行号。
        # - exception=record.exc_info: 如果这条日志带有异常堆栈信息，
        #   就把它原封不动地传给 loguru，保证异常信息完整打印。
        logger.opt(depth=depth, exception=record.exc_info).log(
            level,  # 转换后的日志级别
            record.getMessage()  # 获取原生日志的纯文本消息内容
        )


# ============================================================================
# 5. 强制接管 Python 全局的 logging 配置
# ============================================================================
# logging.basicConfig() 用于配置全局的日志行为：
# - handlers=[InterceptHandler()]: 把我们刚才写的“翻译官”设置为唯一的日志处理器。
#   这意味着所有原生 logging 的日志都会流经这个处理器。
# - level=0: 设置为最低级别（NOTSET），意思是“不要过滤任何级别的日志”。
#   把所有级别的日志都放行，交给 loguru 去决定哪些该打印、哪些该丢弃。
# - force=True: 强制覆盖之前可能已经存在的 logging 配置。
#   如果不加这个，如果 Uvicorn 提前配置过 logging，我们的拦截可能会失效。
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


# ============================================================================
# 6. FastAPI 中间件注册
# ============================================================================
def register_middleware(app: FastAPI) -> FastAPI:
    # 跨域中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        # allow_methods="*",
        allow_headers=["*"],
    )

    #important:设置受信任主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=['127.0.0.1'],
        # allow_methods=["*"],
        # allow_headers=["*"],

    )

    # 自定义日志中间件
    @app.middleware('http')
    async def custom_logging(request: Request, call_next):
        # 为当前请求生成唯一 ID，方便全链路追踪
        request_id = str(uuid4())

        start_time = time.time()

        # 使用 contextualize 将 request_id 绑定到当前请求的日志上下文中
        with logger.contextualize(request_id=request_id):
            logger.info(f"业务来了,准备处理 | {request.method} {request.url}")

            # 针对根路径的特殊处理
            if request.url.path == '/':
                return Response(content="欢迎访问")

            # 传递请求给下一个中间件或路由
            response = await call_next(request)

            processing_time = time.time() - start_time
            logger.info(
                f"处理完毕 | 耗时: {processing_time:.4f}s | 状态码: {response.status_code}"
            )

        return response

    # # tips:自定义授权检查中间件
    # # important:值得注意的是，使用中间件时，无法在中间件内部追踪HTTP异常，它会被抛出异常但不会作为响应返回
    # #   所以如果想要响应,那就用JSONResponse
    # @app.middleware("http")
    # async def authorization(request: Request, call_next):
    #     # tips:如果请求的headers中没有授权头Authorization,那就抛出未授权异常
    #     if not 'Authorization' in request.headers:
    #         return JSONResponse(
    #             content={
    #                 "message": "Not Authorized",
    #                 "resolution": "Please provide the right credentials to proceed"
    #             },
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #         )
    #     response = await call_next(request)
    #     return response
