import os
from typing import Annotated

import requests
from dotenv import load_dotenv
from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette.staticfiles import StaticFiles

load_dotenv()
# THIS NEEDS TO BE EXECUTED BEFORE ANY OTHER IMPORTS

import json

from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from contextlib import asynccontextmanager
from sqlmodel import select, Session
from fastapi import FastAPI, Depends, Request, HTTPException, Form, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth, OAuthError
from sqlalchemy.exc import NoResultFound

from .database import create_tables, engine
from .ai_integration import get_ai_response
# MUST IMPORT ALL MODELS, OTHERWISE RELATIONSHIPS WILL NOT WORK # TODO: find a better way to do this
from .models.incoming_chat_message import IncomingChatMessage
from .models.user import User
from .models.chat_message import ChatMessage


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("start")
    create_tables()
    yield
    print("end")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl='https://accounts.google.com/o/oauth2/auth',
    tokenUrl='https://accounts.google.com/o/oauth2/token',
    scopes={
        "openid": "Access to OpenID Connect authentication",
        "email": "Access to user's email",
        "profile": "Access to user's profile",
    }
)


@app.get('/')
async def homepage():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<script>
function openLoginWindow() {
    const width = 500;
    const height = 600;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2.5;
    
    const popup = window.open(
        'http://localhost:8000/auth/login',
        'Google Login',
        `width=${width},height=${height},left=${left},top=${top}`
    );
    
    const handleMessage = (event) => {
        if (event.origin !== 'http://localhost:8000') {
            return;
        }
        
        if (event.data?.type === 'AUTH_SUCCESS' && event.data?.token) {
            localStorage.setItem('authToken', event.data.token);
        } else if (event.data?.type === 'AUTH_ERROR') {
            console.error(event.data.error);
        } else {
            return;
        }
        
        window.removeEventListener('message', handleMessage);
    };
    
    window.addEventListener('message', handleMessage);
}

function logToken() {
    console.log(localStorage.getItem('authToken'));
}
</script>
<body>
<button
    onclick="openLoginWindow()"
>Login</button>
<button
    onclick="logToken()"
>Log token</button>
</body>
</html>
""")

@app.post('/chat')
async def send_chat_message(request: Request, message: str = Form(...)):
                            # incoming_chat_message: IncomingChatMessage):
    current_session_user = request.session.get('user')
    if not current_session_user:
        raise HTTPException(status_code=401, detail='Unauthorized')

    with Session(engine) as db_session:
        statement = select(User).where(User.id == current_session_user['id'])
        user = db_session.exec(statement).first()

        # get the most recent messages
        statement = select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.send_time.desc()).limit(5)
        recent_messages = db_session.exec(statement).all()
        recent_messages_str = '\n'.join([
            f'{message.sender}@{message.send_time}: {message.message}'
            for message in recent_messages
        ])
        ai_response = await get_ai_response(message, recent_messages_str)

        chat_message_user = ChatMessage(
            user=user,
            message=message,
            sender='user'
        )
        db_session.add(chat_message_user)

        chat_message_ai = ChatMessage(
            user=user,
            message=ai_response,
            sender='ai-assistant'
        )
        db_session.add(chat_message_ai)

        db_session.commit()

    return RedirectResponse(url=request.url_for('homepage'), status_code=303)


@app.post('/delete-chat-message')
async def delete_chat_message(request: Request, message_id: int = Form(...)):
    current_session_user = request.session.get('user')
    if not current_session_user:
        raise HTTPException(status_code=401, detail='Unauthorized')

    with Session(engine) as db_session:
        statement = select(ChatMessage).where(ChatMessage.id == message_id)
        try:
            chat_message = db_session.exec(statement).one()
        except NoResultFound:
            raise HTTPException(status_code=404, detail='Message not found')
        if chat_message.chat.user_id != current_session_user['id']:
            raise HTTPException(status_code=403, detail='Forbidden')
        db_session.delete(chat_message)
        db_session.commit()

    return RedirectResponse(url=request.url_for('homepage'), status_code=303)

@app.get("/auth/login")
async def login(response: Response):
    response.headers["Location"] = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&"
        f"client_id={os.getenv('GOOGLE_CLIENT_ID')}&"
        f"redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    response.status_code = 302
    return response

@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request, code: str):
    token_response = requests.post(
        "https://accounts.google.com/o/oauth2/token",
        data={
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        },
    )
    token_response.raise_for_status()
    token = token_response.json().get("access_token")

    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {token}"},
    )
    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")
    user_data = userinfo_response.json()

    with Session(engine) as db_session:
        statement = select(User).where(User.id == user_data['id'])
        user = db_session.exec(statement).first()
        print(user)
        if not user:
            try:
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    username=user_data['email'].split('@')[0],
                    name=user_data['name'],
                    picture=user_data.get('picture'),
                    google_token=token
                )
            except KeyError as error:
                raise HTTPException(status_code=400, detail=f'KeyError: {error}')
            db_session.add(user)
            db_session.commit()
        else:
            user.google_token = token
            db_session.commit()
        db_session.refresh(user)

    return templates.TemplateResponse(
        request=request,
        name="google_callback.html",
        context={
            "token": token,
            "frontend_origin": os.getenv("FRONTEND_ORIGIN"),
        }
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    print('current_user')
    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {token}"},
    )
    if userinfo_response.status_code != 200:
        print('userinfo_response.status_code:', userinfo_response.status_code)
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    userinfo = userinfo_response.json()
    return User(email=userinfo.get("email"), token=token)

@app.get('/auth/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url=request.url_for('homepage'))