from fastapi_mail import FastMail,ConnectionConfig,MessageSchema,MessageType
from src.config import project_settings
from pathlib import Path
from fastapi import UploadFile

BASE_DIR = Path(__file__).resolve().parent

#step 1:想要配置 FastMail实例,需要准备链接配置
mail_config = ConnectionConfig(
    MAIL_USERNAME=project_settings.MAIL_USERNAME,
    MAIL_PASSWORD=project_settings.MAIL_PASSWORD,
    MAIL_SERVER=project_settings.MAIL_SERVER,
    MAIL_PORT=project_settings.MAIL_PORT,
    MAIL_FROM=project_settings.MAIL_FROM,
    MAIL_STARTTLS=project_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=project_settings.MAIL_SSL_TLS,
    MAIL_FROM_NAME=project_settings.MAIL_FROM_NAME,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(BASE_DIR,'templates').resolve(), #tips:如果想用HTML模板的电子邮件就需要这个
)

#step 2:连接配置准备好之后就用FastMail将连接配置传入进去
mail_server = FastMail(
    config=mail_config,
) #创建一个FastMail实例
#可以看到要求传入的是ConnectionConfig格式
'''
    
    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config
'''

#step 3: 创建能返回MessageSchema的方法
def create_message(
        recipient_list: list[str], #tips:收件人列表
        subject: str, #tips:邮件主题
        body: str, #tips:正文
        # attachments: UploadFile, #tips:附件
):
    message = MessageSchema(
        recipients=recipient_list,
        subject=subject,
        body=body,
        # attachments=attachments
        subtype=MessageType.html #tips:指定文件类型

    )
    return message

#important:重要的是去auth/router中修改路由

#step 4:发送一封电子邮件测试
# mail_server.send_message(
#
# )
#

# 可以看要求传入的是MessageSchema格式
'''
 async def send_message(
        self,
        message: Union[MessageSchema, list[MessageSchema]],
        template_name: Optional[str] = None,
        html_template: Optional[str] = None,
        plain_template: Optional[str] = None,
    ) -> None:'''


