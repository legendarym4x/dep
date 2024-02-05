from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserModel


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    The get_user_by_email function takes an email address and returns the user associated with that email.
    If no such user exists, it returns None.

    :param email: str: Specify the email of the user to be retrieved
    :param db: AsyncSession: Pass in the database session
    :return: A user object if an email is found in the database
    """
    query = select(User).filter_by(email=email)
    user = await db.execute(query)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession = Depends(get_db)):
    """
    The create_user function creates a new user in the database.

    :param body: UserModel: Validate the request body
    :param db: AsyncSession: Get the database session
    :return: A user object
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the refresh token for a user.

    :param user: User: Specify the type of user
    :param token: str | None: Specify that the token parameter can be a string or none
    :param db: AsyncSession: Make sure that the database session is passed to the function
    :return: A user object with the updated refresh token
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession):
    """
    The confirmed_email function takes in an email and a database session,
    and sets the confirmed field of the user with that email to True.


    :param email: str: Specify the email of the user that is to be confirmed
    :param db: AsyncSession: Pass in the database session
    :return: The user object
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    The update_avatar_url function updates the avatar url of a user.

    :param email: str: Find the user in the database
    :param url: str | None: Set the avatar url for a user
    :param db: AsyncSession: Pass the database connection into the function
    :return: The updated user object
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def set_new_password(email: str, new_password: str, db: AsyncSession):
    """
    The set_new_password function takes in an email and a new password,
        then updates the user's password to the new one.

    :param email: str: Find the user in the database
    :param new_password: str: Set the new password for the user
    :param db: AsyncSession: Pass in the database session to the function
    :return: The user object
    """
    user = await get_user_by_email(email, db)
    user.password = new_password
    await db.commit()
    return user


async def update_reset_token(user: User, reset_token, db: AsyncSession):
    """
    The update_reset_token function updates the password_reset_token field of a user in the database.

    :param user: User: Pass the user object to the function
    :param reset_token: Update the password_reset_token field in the user table
    :param db: AsyncSession: Pass in the database session to use for this function
    :return: The user object
    """
    user.password_reset_token = reset_token
    await db.commit()
    return user
