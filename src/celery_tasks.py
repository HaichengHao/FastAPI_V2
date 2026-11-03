from celery import Celery
from src.mail import create_message,mail_server
from asgiref.sync import async_to_sync #使用异步转同步函数
from loguru import logger
#要创建一个Celery应用，作为celery类的实例
#其实它的写法和FastAPI差不多
c_app = Celery()

c_app.config_from_object('src.config') #tips:设置celery应用的配置文件的加载位置,我们是在src.config中设置的


#创建第一个任务

@c_app.task()
def send_email(
        u_bcc_list: list[str],
        u_subject:str,
        u_html_msg:str,
):
    logger.info("开始执行邮件发送服务")
    message = create_message(
        bcc_list=u_bcc_list, #收件人列表
        subject=u_subject, #主题
        body=u_html_msg #邮件消息内容

    )

    #由于send_message是协程，所以需要将其转换为在同步函数中可以运行的代码才行
    #这时候就需要asgiref的sync方法中的async_to_sync，既异步转同步函数
    # mail_server.send_message(message)  原来的发送方式不再适用

    async_to_sync(mail_server.send_message)(message)
    logger.info("邮件发送结束")






