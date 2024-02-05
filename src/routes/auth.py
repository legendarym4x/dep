from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import UserModel, TokenModel, UserResponse, RequestEmail, ResetPassword
from src.services.auth import auth_service, auth_password
from src.services.email import send_email, send_reset_password_email

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        It takes in a UserModel object, which is validated by pydantic.
        The password is hashed using Argon2 and stored as such.


    :param body: UserModel: Get the data from the request body
    :param bt: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the request
    :param db: AsyncSession: Get the database session
    :return: A new user object
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    The login function is used to authenticate a user.
        It takes in the username and password of the user, verifies them against
        those stored in the database, and returns an access token if successful.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: AsyncSession: Get the database session
    :return: A dictionary with the access token, refresh token and the type of token
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.
    It takes in a refresh token and returns a new access_token,
    refresh_token pair. The function first decodes the refresh token
    to get the email of the user who owns it. It then gets that user from
    the database and checks if their stored refresh_token matches what was passed in. If not, it raises an error because this means that either:

    :param credentials: HTTPAuthorizationCredentials: Get the credentials from the request header
    :param db: AsyncSession: Get the database session
    :return: A new access token and refresh token
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
    It takes the token from the URL and uses it to get the user's email address.
    Then, it checks if that user exists in our database, and if they do not exist, we return an error message.
    If they do exist but their account has already been confirmed, we return a success message saying so.
    Otherwise, (if they exist and their account has not yet been confirmed), we update their record in our database
    by setting &quot;confirmed&quot; to True for that particular record.

    :param token: str: Get the token from the url
    :param db: AsyncSession: Get the database session
    :return: A json object with the message
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function is used to send email to the user with a link that will allow them
    to confirm their email address. The function takes in a RequestEmail object, which contains the
    email of the user who wants to confirm their account. It then checks if there is already a confirmed
    user with that email address, and if so returns an error message saying as much. If not, it sends
    an email containing a confirmation link.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Get a database session from the dependency injection container
    :return: A message if the user's email is already confirmed,
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.get('/{username}')
async def request_email(username: str, response: Response, db: AsyncSession = Depends(get_db)):
    """
    The request_email function is called when the user opens an email.
        It saves a record in the database that this user opened their email.
        This function returns a PNG image to be displayed in the browser.

    :param username: str: Get the username from the url
    :param response: Response: Return a response to the client
    :param db: AsyncSession: Get the database session
    :return: A png image that is used as a pixel to check if the email was opened
    """
    print('----------------------------------------------')
    print(f"{username} Save 'He opened email' in database")
    print('----------------------------------------------')
    return FileResponse('src/static/open_check.png', media_type='image/png', content_disposition_type='inline')


@router.post('/reset_password')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function is used to send a reset password email to the user.
        The function takes in an email and sends a reset password link if the email exists in our database.
        If it does not exist, then we return an error message.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Get the database session
    :return: A message to the user
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user:
        background_tasks.add_task(send_reset_password_email, user.email, user.username, str(request.base_url),
                                  extra_data={"subject": "Confirmation", "template_name": "reset_password.html"})
        return {"message": "Check your email for the next step."}
    return {"message": "Your email is incorrect"}


@router.get('/reset_password/{token}')
async def password_reset_confirm(token: str, db: AsyncSession = Depends(get_db)):
    """
    The password_reset_confirm function is used to reset a user's password.
        It takes in the token that was sent to the user's email address and uses it
        to get their email address from auth_service.get_email_from_token(). Then,
        it gets the User object for that email from repositories_users.get_user() and
        creates a new reset token using auth service create token function with data={&quot;sub&quot;: user.email}.

    :param token: str: Get the user's email from the token
    :param db: AsyncSession: Pass the database session to the function
    :return: A reset_password_token
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    reset_password_token = auth_service.create_email_token(data={"sub": user.email})
    await repositories_users.update_reset_token(user, reset_password_token, db)
    return {'reset_password_token': reset_password_token}


@router.post('/set_new_password')
async def update_password(request: ResetPassword, db: AsyncSession = Depends(get_db)):
    """
    The update_password function takes a ResetPassword object and updates the password of the user
        associated with that email. It also checks to make sure that the reset_password_token is valid,
        and if it is not, raises an HTTPException. If it is valid, then we check to see if new_password
        matches confirm_password. If they do not match, we raise an HTTPException again.

    :param request: ResetPassword: Get the reset_password_token and new password
    :param db: AsyncSession: Get the database session
    :return: A dictionary containing the message &quot;password successfully updated&quot;
    """
    token = request.reset_password_token
    email = auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    check_token = user.password_reset_token
    if check_token != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token")
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="passwords do not match")

    new_password = auth_password.get_hash_password(request.new_password)
    await repositories_users.update_password(user, new_password, db)
    await repositories_users.update_reset_token(user, None, db)
    return {"message": "Password successfully updated"}
