import os
from dotenv import load_dotenv

load_dotenv()
# THIS NEEDS TO BE EXECUTED BEFORE ANY OTHER IMPORTS

import json

from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from contextlib import asynccontextmanager
from sqlmodel import select, Session
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

from .database import create_tables, engine
# MUST IMPORT ALL MODELS, OTHERWISE RELATIONSHIPS WILL NOT WORK # TODO: find a better way to do this
from .models.user import User
from .models.chat import Chat
from .models.chat_message import ChatMessage


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("start")
    create_tables()
    yield
    print("end")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

config = Config('.env')
oauth = OAuth(config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'},
)


@app.get('/')
async def homepage(request: Request):
    user = request.session.get('user')
    if user:
        data = json.dumps(user)
        html = (
            '<h1>Logged in</h1>'
            f'<pre>{data}</pre>'
            f'<a href="{request.url_for("logout")}">logout</a>'
        )
        return HTMLResponse(html)
    return HTMLResponse(f'<a href="{request.url_for("login")}">login</a>')

@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user_data = token['userinfo']
    # check user in database
    # if not exists, create user
    with Session(engine) as session:
        statement = select(User).where(User.id == user_data['sub'])
        user = session.exec(statement).first()
        if not user:
            try:
                user = User(
                    id=user_data['sub'],
                    email=user_data['email'],
                    username=user_data['email'].split('@')[0],
                    name=user_data['name'],
                    picture=user_data.get('picture')
                )
            except KeyError as error:
                raise HTTPException(status_code=400, detail=f'KeyError: {error}')
            session.add(user)
            session.commit()
            session.refresh(user)
    request.session['user'] = user.model_dump()

    return RedirectResponse(url=request.url_for('homepage'))

@app.get('/auth/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url=request.url_for('homepage'))