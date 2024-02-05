import os
from ipaddress import ip_address
from pathlib import Path
from typing import Callable

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db
from src.routes import contacts, auth, users
from src.conf.config import config

app = FastAPI()

origins = ["*"]

app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

# If you want to create a blacklist of required IP addresses

# banned_ips = [ip_address("192.168.1.1"), ip_address("192.168.1.2"), ip_address("127.0.0.1")]

# @app.middleware("http")
# async def ban_ips(request: Request, call_next: Callable):
#     ip = ip_address(request.client.host)
#     if ip in banned_ips:
#         return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"})
#     response = await call_next(request)
#     return response


BASE_DIR = Path(__file__).parent
directory = BASE_DIR.joinpath("src").joinpath("static")
app.mount("/static", StaticFiles(directory=BASE_DIR/"src"/"static"), name="static")

app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are needed by your app, such as databases or caches.

    :return: A coroutine, so you need to call it with asyncio
    """
    r = await redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0, password=config.REDIS_PASSWORD,
                          encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)


templates = Jinja2Templates(directory=BASE_DIR/"src"/"templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    The index function is executed when someone visits the root URL of our site: http://localhost:8000/
    It returns a TemplateResponse, which contains both a template and values to be used when rendering it.
    The first argument passed to the function is request, which contains information about the current web request that has been made.
    We pass this along in case we need any information from it (like POST data), but for now we're just passing an empty dictionary as context.

    :param request: Request: Pass the request object to the template
    :return: A templateResponse object
    """
    return templates.TemplateResponse("index.html", {"request": request, "our": "Build by group WebPython #17"})


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    The healthchecker function is a simple function that checks the health of the database.
    It does this by making a request to the database and checking if it returns any results.
    If it doesn't, then we know something is wrong with our connection.

    :param db: AsyncSession: Inject the database session into the function
    :return: A dictionary with a message
    """
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")
