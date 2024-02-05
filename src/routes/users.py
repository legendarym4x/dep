import pickle

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserResponse
from src.services.auth import auth_service
from src.conf.config import config
from src.repository import users as repositories_users

router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(cloud_name=config.CLOUDINARY_NAME, api_key=config.CLOUDINARY_API_KEY,
                  api_secret=config.CLOUDINARY_API_SECRET, secure=True)


@router.get("/me", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=2, seconds=20))])
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """
    The get_current_user function is a dependency that will be injected into the
    get_current_user endpoint. It uses the auth_service to retrieve the current user,
    and returns it if found.

    :param user: User: Pass the user object to the function
    :return: The user object that is stored in the token
    """
    return user


@router.patch("/avatar", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=2, seconds=20))])
async def update_avatar(file: UploadFile = File(), user: User = Depends(auth_service.get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """
    The update_avatar function is used to update the avatar of a user.
    The function takes in an UploadFile object, which contains the file that will be uploaded to Cloudinary.
    It also takes in a User object, which is obtained from auth_service's get_current_user function.
    Finally, it takes in an AsyncSession object, which is obtained from get_db().

    :param file: UploadFile: Upload the file to cloudinary
    :param user: User: Get the user from the database
    :param db: AsyncSession: Get a connection to the database
    :return: The updated user object
    """
    public_id = f"Web17/{user.email}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, owerite=True)
    print(res)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(width=250, height=250, crop="fill",
                                                              version=res.get("version"))
    user = await repositories_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user
