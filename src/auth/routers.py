from datetime import datetime
from src.errors import InvalidToken, UserNotFound
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.responses import JSONResponse
from src.auth.schemas import UserCreatedSchema, PasswordConfirmSchema, UserLoginSchema, RespSchema, EmailSchema, \
    PasswordResetSchema
from src.db.main import get_session
from src.auth.service import user_service
from src.auth.dependencies import access_token_bearer, refresh_token_bearer, get_current_user, role_checker
from src.auth.utils import create_access_token, create_url_safe_token, decode_url_safe_token
from src.db.redis import add_jti_to_blocklist
from src.mail import create_message, mail_server
from src.errors import InvalidCredentials
from src.config import project_settings
from src.auth.utils import generate_password_hash
from fastapi import Request
auth_router = APIRouter(
    tags=['auth']
)


# tips:定义邮件发送路由
@auth_router.post('/send_mail')
async def send_mail(emails: EmailSchema):
    emails_addr = emails.email_address
    mailbody = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>邮件通知</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f6f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td align="center" style="background-color: #ffffff; border-radius: 12px; padding: 40px 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                    <!-- Logo/Header -->
                    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td align="center" style="padding-bottom: 30px;">
                                <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; display: inline-block; line-height: 60px; font-size: 28px; color: #ffffff; font-weight: bold;">📧</div>
                                <h1 style="color: #1a1a2e; font-size: 24px; margin: 20px 0 0 0; font-weight: 600;">NIKOFOX 邮件通知</h1>
                            </td>
                        </tr>
                        
                        <!-- 分隔线 -->
                        <tr>
                            <td align="center" style="padding-bottom: 30px;">
                                <div style="width: 80px; height: 3px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 2px;"></div>
                            </td>
                        </tr>
                        
                        <!-- 正文内容 -->
                        <tr>
                            <td style="padding-bottom: 30px;">
                                <p style="color: #2d3748; font-size: 16px; line-height: 1.8; margin: 0 0 20px 0;">
                                    您好！
                                </p>
                                <p style="color: #2d3748; font-size: 16px; line-height: 1.8; margin: 0 0 20px 0;">
                                    这是一封来自 <strong style="color: #667eea;">FastAPI V2</strong> 的测试邮件。
                                </p>
                                <div style="background: #f7fafc; border-left: 4px solid #667eea; padding: 16px 20px; border-radius: 4px; margin: 20px 0;">
                                    <p style="color: #2d3748; font-size: 15px; line-height: 1.6; margin: 0;">
                                        📌 这是一条测试消息，如果您收到此邮件，说明邮件服务配置成功！
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- 按钮 -->
                        <tr>
                            <td align="center" style="padding-bottom: 30px;">
                                <a href="#" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-size: 16px; font-weight: 500; transition: all 0.3s ease;">
                                    查看详情 →
                                </a>
                            </td>
                        </tr>
                        
                        <!-- 底部信息 -->
                        <tr>
                            <td align="center" style="border-top: 1px solid #e2e8f0; padding-top: 20px;">
                                <p style="color: #718096; font-size: 13px; line-height: 1.6; margin: 0;">
                                    此邮件由 NIKOFOX FastAPI V2 系统自动发送<br>
                                    请勿回复此邮件
                                </p>
                                <p style="color: #a0aec0; font-size: 12px; margin: 10px 0 0 0;">
                                    © 2026 NIKOFOX. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    message = create_message(bcc_list=emails_addr, subject='test mail', body=mailbody)
    await mail_server.send_message(message)
    return {
        'message': 'success send mail',
    }


# tips:定义注册路由
# @auth_router.post('/signup', response_model=RespSchema, status_code=status.HTTP_201_CREATED)
@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)  # 由于做了邮件改造，所以这里不再返回new_user,自然不能用RespSchema了,不然是会报错的
async def create_user_Account(
        user_data: UserCreatedSchema,
        session: Annotated[AsyncSession, Depends(get_session)],
        request: Request,
):
    email = user_data.email
    # tips:先查一下看看该用户有没有被注册
    result = await user_service.get_user_by_email(email, session=session)
    if result:  # TIPS:如果结果不为空，说明用户已经存在了
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email already registered")
    else:  # 如果不为空那就开始注册逻辑链
        # 调用创建服务创建用户
        new_user = await user_service.create_user(user_data, session=session)

        # 生成safetoken
        token = create_url_safe_token(
            {
                'email': email,

            }
        )
        # ---------
        # 改造,引入通过电子邮件验证用户账户
        # link = f"http://{project_settings.DOMAIN_NAME}/api/v1/auth/verify/{token}"
        link = str(request.url_for('verify_user_account', token=token)) #被静态硬编码坑惨了，所以换动态的，不然老验证不过去
        html_msg = f"""
        <html>
            <body>
                <h1>验证你的电子邮件</h1>
                <p>点此<a href="{link}">链接</a>验证你的邮箱</a></p>
            </body>
        </html>
        """
        # 构建信息，发送给用户
        message = create_message(
            bcc_list=[email],
            subject="Verify your Email",
            body=html_msg

        )

        await mail_server.send_message(message)

        return {
            "message": "Account created successfully! Check email verify your count",
            "user": new_user
        }
        # ---------

        # return new_user


# 创建MPI端点,实现邮箱认证服务
@auth_router.get('/verify/{token}')
async def verify_user_account(token: str, session: Annotated[AsyncSession, Depends(get_session)]):
    # tips:解码收到的token
    token_data =  decode_url_safe_token(token)

    user_email = token_data.get('email')
    if user_email:
        user = await user_service.get_user_by_email(user_email, session=session)
        if not user:
            raise UserNotFound()
        # 如果用户存在，那就调用service来更新用户的信息
        await user_service.update_user(user, {'is_verified': True}, session=session)

        return JSONResponse(
            content={
                "message": "Account verified successfully!!"
            },
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        content={
            "message": "Something went wrong :("
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR

    )


# tips:定义jwt认证路由
@auth_router.post('/login')
async def login_user(login_data: UserLoginSchema, session: Annotated[AsyncSession, Depends(get_session)]):
    result = await user_service.login_service(login_data, session=session)
    return result


@auth_router.post('/refresh_token')
async def refresh_token(token_details: Annotated[dict, Depends(refresh_token_bearer)]):
    expiry_timestamp = token_details['exp']  # tips:拿到解码token_data中的payload['exp']
    print(expiry_timestamp)
    # important:利用fromtimestamp将时间戳转换为日期时间对象
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():  # tips:如果过期时间大于当前时间,那么就创建一个新的访问令牌
        new_access_token = create_access_token(
            user_data=token_details['user'],
        )
        return JSONResponse(
            content={
                "access_token": new_access_token,
            }
        )

    # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or Expired token")
    raise InvalidToken()


# ----------基于用户身份进行鉴权分块代码----------------#

# tips:获取当前用户
@auth_router.get('/me', response_model=RespSchema)
async def get_now_user(user: Annotated[dict, Depends(get_current_user)],
                       _: Annotated[bool, Depends(role_checker)]):  # important:使用占位符号,表示不关心变量,而是必须执行依赖项目,检查角色
    # async def get_now_user(user=Depends(get_current_user),_:bool=Depends(role_checker)):
    return user


# ----------基于用户身份进行鉴权分块代码----------------#
@auth_router.get('/logout')
async def revoke_token(token_details: Annotated[dict, Depends(access_token_bearer)]):
    jti = token_details['jti']

    # tips:拿到了jti之后把它加在阻止列表中
    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={
            "message": "Logged out successfully",  # tips:返回成功注销
        },
        status_code=status.HTTP_200_OK
    )


# ---------------------密码重置---------------------

"""
1.获取用户的邮箱地址 ->密码重置请求,需要让ta们发送邮箱
2.发送密码重置连接
3.通过post请求提供信息，来重置密码 -> 密码重置确认

"""


@auth_router.post('/pwd-rest-request')
async def pwd_rest(email_data: PasswordResetSchema, session: Annotated[AsyncSession, Depends(get_session)],request:Request):
    email = email_data.email
    # tips:先查一下看看该用户有没有被注册
    result = await user_service.get_user_by_email(email, session=session)
    if result:  # TIPS:如果结果不为空，说明用户已经存在了
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email already registered")
    else:
        new_user = await user_service.create_user(email_data, session=session)

        # 生成safetoken
        token = create_url_safe_token(
            {
                'email': email,

            }
        )
        # ---------
        # 改造,引入密码重置认证，对应路由在下方实现
        # link = f"http://{project_settings.DOMAIN_NAME}/api/v1/auth/pwd_reset_confirm/{token}"
        link = str(request.url_for('pwd_reset_confirm', token=token)) #被静态硬编码坑惨了，所以换动态的，不然老验证不过去

        html_msg = f"""
           <html>
               <body>
                   <h1>重置您的密码</h1>
                   <p>点此<a href="{link}">链接</a>重置密码</a></p>
               </body>
           </html>
           """
        # 构建信息，发送给用户
        message = create_message(
            bcc_list=[email],
            subject="Verify your Email",
            body=html_msg

        )

        await mail_server.send_message(message)

        return JSONResponse(
            content={
                "message": "Account created successfully! Check email verify your count",
                "user": new_user
            },
            status_code=status.HTTP_200_OK,
        )


# 实现密码重置确认的路由

@auth_router.post('/pwd_rest_confirm/{token}')
async def pwd_reset(token: str, pwd_data: PasswordConfirmSchema,
                    session: Annotated[AsyncSession, Depends(get_session)]):
    if pwd_data.new_pwd != pwd_data.confirm_new_pwd:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password not match")
    token_data = decode_url_safe_token(token)
    user_email = token_data.get('email')
    if  user_email:
        user = await user_service.get_user_by_email(user_email, session=session)
        if not user:
            raise UserNotFound()
        pwd_hashed = generate_password_hash(pwd_data.confirm_new_pwd)
        user_service.update_user(user, user_data={'password_hash': pwd_hashed}, session=session)
        return JSONResponse(
            content={
                "message": "Password reset successfully",
            },
            status_code=status.HTTP_200_OK,
        )
    return JSONResponse(
        content={
            "message":"Error occured while trying to reset password",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
