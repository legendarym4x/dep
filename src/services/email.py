from pathlib import Path

from fastapi import HTTPException, status, Depends
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from pydantic import EmailStr

from src.database.db import get_db
from src.repository.users import get_user_by_email
from src.services.auth import auth_service
from src.conf.config import config
from src.repository import users as repository_users


conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="Users System",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    The send_email function sends an email to the user with a link to verify their email address.
        The function takes in three parameters:
            -email: the user's email address, which is used as a recipient for the message and also as part of
                the token that will be sent in order to verify their account. This parameter must be of type EmailStr,
                which is defined by pydantic and ensures that it is a valid email format. If not, then an error will be raised.

    :param email: EmailStr: Specify the email address of the user
    :param username: str: Pass the username to the template
    :param host: str: Pass the hostname of the server to be used in the email link
    :return: A coroutine object, which is not a string
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_reset_password_email(email: EmailStr, username: str, host: str, extra_data: dict = None):
    """
    The send_reset_password_email function sends an email to the user with a link to reset their password.

    :param email: EmailStr: Identify the user's email address
    :param username: str: Pass the username of the user to be emailed
    :param host: str: Pass the hostname of the website to the template
    :param extra_data: dict: Send extra data to the template
    :return: A boolean value
    """
    try:
        token_reset = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Reset Password",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_reset},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as err:
        print(err)
