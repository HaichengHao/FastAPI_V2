我看了你的 Celery 启动日志和 `c_app` 代码，这次问题比较明确：不是 Redis 连接错误，也不是你的邮件发送函数写错，而是 Celery 默认的 `prefork` 进程池在 Windows 环境下出现了兼容性问题。

你使用的是：

- Windows 11
- Python 3.12
- Celery 5.6.3
- Redis：`127.0.0.1:65522`
- Celery 默认进程池：`prefork`

Celery 官方明确表示 Windows 不是正式支持的平台，并建议 Windows 用户遇到进程池问题时尝试 `solo` 或 `threads`。

[image](https://www.google.com/s2/favicons?domain=https://docs.celeryq.dev\&sz=32)

Celery 5.6.3 documentation+1



## 一、先解决问题：修改 Celery 启动命令

你现在的启动命令：

```
celery -A src.celery_tasks.c_app worker
```

日志显示：

```
concurrency: 18 (prefork)

ERROR/SpawnPoolWorker-11
PermissionError: [WinError 5] 拒绝访问
```

这是 Celery 默认创建 18 个工作进程时，在 `billiard` 的进程间同步操作中发生的错误。

### 方案一：使用 solo 模式（推荐先尝试）

直接修改为：

```
celery -A src.celery_tasks.c_app worker --loglevel=info --pool=solo
```

`solo` 表示任务在 Worker 主线程中顺序执行，不再创建额外的工作子进程。

正常启动后应该看到：

```
-------------- celery@aya v5.6.3
--- ***** -----
...
.> transport: redis://127.0.0.1:65522/0
.> results:   redis://127.0.0.1:65522/0
.> concurrency: 1 (solo)

[registered tasks]
  . src.celery_tasks.send_email

[INFO/MainProcess] celery@aya ready.
```

这是预期输出示例，实际任务名称取决于你的模块路径和 Celery 注册情况。

对于你目前的邮件发送任务，先用 `solo` 完全足够验证功能。

### 方案二：使用 threads 模式（支持并发）

由于邮件发送属于典型的 I/O 密集型任务，你也可以使用：

```
celery -A src.celery_tasks.c_app worker --loglevel=info --pool=threads --concurrency=4
```

这样会使用 4 个线程执行任务，而不是创建 18 个独立进程。

| 模式               | Windows 适用性  | 特点                     |
| ---------------- | ------------ | ---------------------- |
| `prefork`        | 不推荐          | 多进程，Windows 下容易遇到兼容性问题 |
| `solo`           | 适合本地调试       | 单线程、任务顺序执行             |
| `threads`        | 适合邮件等 I/O 任务 | 多线程并发执行                |
| `prefork`（Linux） | 推荐生产环境使用     | 多进程隔离，功能支持更完整          |

需要注意，`threads` 与 `solo` 都有一定的功能限制，例如不提供与 `prefork` 完全一致的软超时能力。

[image](https://www.google.com/s2/favicons?domain=https://docs.celeryq.dev\&sz=32)

Celery 5.6.3 documentation



## 二、你的 Celery 代码是否需要修改？

你目前的代码：

```
from celery import Celeryfrom src.mail import create_message, mail_serverfrom asgiref.sync import async_to_syncc_app = Celery()c_app.config_from_object('src.config')@c_app.task()def send_email(    u_bcc_list: list[str],    u_subject: str,    u_html_msg: str,):    message = create_message(        bcc_list=u_bcc_list,        subject=u_subject,        body=u_html_msg    )    async_to_sync(mail_server.send_message)(message)
```

这段代码的基本思路是正确的。

因为 Celery 的普通任务函数是同步执行的，而你的邮件发送方法：

```
mail_server.send_message(message)
```

是异步协程，所以需要适配。

你这里使用：

```
async_to_sync(mail_server.send_message)(message)
```

是可行的。

不过我建议做一些小调整。

### 推荐修改后的 `src/celery_tasks.py`

```
from celery import Celeryfrom asgiref.sync import async_to_syncfrom loguru import loggerfrom src.mail import create_message, mail_server# 初始化 Celeryc_app = Celery("fastapi_mail_worker")# 加载 Celery 配置c_app.config_from_object("src.config")@c_app.task(    bind=True,    name="send_email",    autoretry_for=(ConnectionError, TimeoutError),    retry_backoff=True,    retry_kwargs={"max_retries": 3})def send_email(    self,    u_bcc_list: list[str],    u_subject: str,    u_html_msg: str,):    logger.info("开始执行邮件发送任务")    message = create_message(        bcc_list=u_bcc_list,        subject=u_subject,        body=u_html_msg    )    async_to_sync(mail_server.send_message)(message)    logger.info("邮件发送任务执行完成")    return {"status": "success"}
```

这里主要改动是：

1. 显式指定 Celery 应用名称，方便管理。
2. 显式指定任务名称 `send_email`，避免任务路径变化影响调用。
3. 对部分暂时性网络错误增加自动重试。
4. 增加日志，方便定位任务是否执行成功。

注意：SMTP 发送可能出现邮件已被服务端接受、但客户端没有收到确认的情况，因此自动重试存在重复发信风险。生产环境还需要限流、幂等控制，并且不要将收件人地址、重置 Token 和邮件正文直接写入日志。

## 三、FastAPI 应该如何调用 Celery？

这里我还想提醒你一个容易忽略的问题。

你之前的密码重置接口是：

```
await mail_server.send_message(message)
```

这种写法意味着 FastAPI 要等待邮件发送完成，才能返回 HTTP 响应。

现在引入 Celery 后，应该改成把邮件发送任务投递到 Redis。

### 修改你的邮件发送逻辑

```
from src.celery_tasks import send_email# 原来# await mail_server.send_message(message)# 改成send_email.delay(    u_bcc_list=[email],    u_subject="Password Reset",    u_html_msg=html_msg)
```

这里需要注意：Celery 的 `.delay()` 不需要 `await`。

这是因为它是同步任务投递接口，而不是 Python 协程。

你还可以拿到任务 ID：

```
task = send_email.delay(    u_bcc_list=[email],    u_subject="Password Reset",    u_html_msg=html_msg)print("Celery Task ID:", task.id)
```

此时整个流程变成：

FastAPI

用户请求发送邮件

Celery Task.delay()

将邮件任务投递到 Redis

Redis Broker

保存待执行的邮件任务

Celery Worker

获取任务，调用邮件发送服务

SMTP 邮件发送

FastAPI 在任务成功投递到 Broker 后就可以响应客户端，不必等待 SMTP 发送完成。

但是要注意：任务投递成功不等于邮件已经发送成功。

## 四、检查 Redis 和 Celery 是否正常工作

你当前 Celery 日志显示：

```
transport: redis://127.0.0.1:65522/0
results:   redis://127.0.0.1:65522/0
```

说明 Celery 已经读取到了 Redis 的连接配置，但这还不能证明 Worker 能正常消费任务。

你可以先执行：

```
docker ps
```

确认 Redis Stack 容器运行正常。

然后使用：

```
docker exec -it <redis容器名> redis-cli ping
```

如果 Redis 配置了认证，需要带相应认证参数。

正常返回：

```
PONG
```

接下来启动 Celery：

```
celery -A src.celery_tasks.c_app worker --loglevel=info --pool=solo
```

再打开另一个 PowerShell 窗口：

```
python
```

输入：

```
from src.celery_tasks import send_emailtask = send_email.delay(    u_bcc_list=["你的测试邮箱@qq.com"],    u_subject="Celery Test",    u_html_msg="<h1>Celery邮件服务测试成功</h1>")print(task.id)
```

如果一切正常，Worker 日志会出现类似：

```
Task send_email[xxxxxxxx] received
Task send_email[xxxxxxxx] succeeded
```

随后邮箱中应该收到测试邮件。

## 五、如果后面需要生产部署

你现在是在 Windows 11 上开发，但后面如果部署到 Ubuntu + Docker，我更推荐使用 Linux 环境运行 Celery Worker。

例如：

```
celery -A src.celery_tasks.c_app worker \
    --loglevel=info \
    --pool=prefork \
    --concurrency=4
```

Linux 下的 `prefork` 是 Celery 推荐的常规并发模式，适合正式部署。

[image](https://www.google.com/s2/favicons?domain=https://docs.celeryq.dev\&sz=32)

Celery 5.6.2 documentation



需要注意，如果你把 Redis 也部署到 Docker 中，容器里的 `127.0.0.1` 指的是容器自身，通常需要将 Broker URL 改成 Compose 网络中的 Redis 服务名。

## 六、现在你只需要先做这一件事

把原来的：

```
celery -A src.celery_tasks.c_app worker
```

改成：

```
celery -A src.celery_tasks.c_app worker --loglevel=info --pool=solo
```

不需要修改 Celery 源代码，也不需要重装 Python、Redis 或 Celery。

这个启动参数就是针对你当前 `billiard` 进程池 `WinError 5` 的最小改动方案。

如果能够正常启动，再运行第三部分的 `.delay()` 测试，我们就能确认 FastAPI → Redis → Celery Worker → SMTP 这条异步邮件服务链路是否真正打通。