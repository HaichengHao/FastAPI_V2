from typing import Any, Callable

from fastapi import FastAPI,status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
class BooklyException(Exception):
    """
    this is the base exception class for all other exceptions
    """
    pass
class InvalidToken(BooklyException):
    """User has provided an invalid token"""
    pass

class RevokedToken(BooklyException):
    """User has provided a revoked token"""
    pass
class AccessTokenRequired(BooklyException):
    """User has provided a refresh token when an access token is required"""
    pass
class RefreshTokenRequired(BooklyException):
    """User has provided an access token when an access token is required"""
    pass

class UserAlreadyExists(BooklyException):
    """User has provided an email for a user who already exists"""
    pass

class InsufficientPermission(BooklyException):
    """User does not have the necessary permissions to perform an action"""
    pass

class BookNotFound(BooklyException):
    """Book not found exception"""
    pass


class UserNotFound(BooklyException):
    """User not found exception"""
    pass

class InvalidCredentials(BooklyException):
    """Invalid credentials exception"""
    pass

class BookAlreadyExists(BooklyException):
    """Book already exists exception"""
    pass


async def create_exception_handler(status_code:int,initial_detail:Any) -> Callable[[Request,Exception],JSONResponse]:
    async def exception_handler(request:Request,exc:BooklyException):
        return JSONResponse(
            content=initial_detail,
            status_code=status_code,
        )
    return exception_handler


def register_all_errors(app:FastAPI):
    app.add_exception_handler(
        UserAlreadyExists,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                'message': 'User with email already exists.',
                'error_code': 'user_already_exists',
            }
        )

    )

    app.add_exception_handler(
        BookNotFound,
        handler=create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                'message': 'Book not found.',
                'error_code': 'book_not_found',
            }
        )

    )

    app.add_exception_handler(
        BookAlreadyExists,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                'message': 'User already exists.',
                'error_code': 'user_already_exists',
                'resolution': 'Please provide a valid user.'
            }
        )

    )
    app.add_exception_handler(
        UserNotFound,
        handler=create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                'message': 'User not found.',
                'error_code': 'user_not_found',
                'resolution': 'Please provide a valid user.'
            }
        )

    )

    app.add_exception_handler(
        InvalidCredentials,
        handler=create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                'message': 'Invalid credentials.',
                'error_code': 'invalid_credentials',

            }
        )

    )

    app.add_exception_handler(
        InvalidToken,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                'message': 'Token is invalid.',
                'error_code': 'invalid_token',
                'resolution': 'Please get new token'
            }
        )

    )

    app.add_exception_handler(
        RevokedToken,
        handler=create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                'message': 'Token is invalid or has been revoked.',
                'error_code': 'token_revoked',
                'resolution': 'Please get new token'
            }
        )

    )

    app.add_exception_handler(
        AccessTokenRequired,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                'message': 'Please provide a valid access token.',
                'error_code': 'access_token_required',
                'resolution': 'Please get new access token'
            }
        )

    )

    app.add_exception_handler(
        RefreshTokenRequired,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                'message': 'Please provide a valid refresh token.',
                'error_code': 'refresh_token_required',
                'resolution': 'Please get new refresh token'
            }
        )

    )

    app.add_exception_handler(
        InsufficientPermission,
        handler=create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                'message': 'Insufficient permissions.',
                'error_code': 'permission_denied',
                'resolution': 'Please provide a valid permission.'
            }
        )

    )