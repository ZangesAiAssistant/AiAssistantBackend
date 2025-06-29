from dotenv import load_dotenv

load_dotenv()
# THIS NEEDS TO BE EXECUTED BEFORE ANY OTHER IMPORTS

import os
from typing import Annotated

import requests
from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from contextlib import asynccontextmanager
from sqlmodel import select, Session
from fastapi import FastAPI, Depends, Request, HTTPException, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import NoResultFound
import logfire

from .database import engine
from .ai_integration import get_ai_response
from .calendar_integration import fetch_google_calendar_events, create_google_calendar_event
# MUST IMPORT ALL MODELS, OTHERWISE RELATIONSHIPS WILL NOT WORK # TODO: find a better way to do this
from .models.user import User
from .models.chat_message import ChatMessage
from .models.incoming_chat_message import IncomingChatMessage
from .models.select_chat_message import SelectChatMessage
from .models.event_creation_parameters import EventCreationParameters


@asynccontextmanager
async def lifespan(app: FastAPI):
    logfire.info("FastAPI lifespan started")
    yield
    logfire.info("FastAPI lifespan ended")

app = FastAPI(lifespan=lifespan)

logfire.configure()
logfire.instrument_fastapi(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

origins = [os.getenv("FRONTEND_ORIGIN")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

scopes = {
    "openid": "Access to OpenID Connect authentication",
    "email": "Access to user's email",
    "profile": "Access to user's profile",
    "https://www.googleapis.com/auth/calendar.readonly": "Read-only access to calendar metadata",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly": "Read-only access to calendar list metadata",
    "https://www.googleapis.com/auth/calendar.events.readonly": "Read-only access to calendar events",
    "https://www.googleapis.com/auth/calendar.app.created": "Full access to a secondary calendar",
    "https://www.googleapis.com/auth/gmail.readonly": "Read-only access to Gmail",
    "https://www.googleapis.com/auth/gmail.compose": "Compose and send emails",
    "https://www.googleapis.com/auth/gmail.labels": "Manage labels",
}
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl='https://accounts.google.com/o/oauth2/auth',
    tokenUrl='https://accounts.google.com/o/oauth2/token',
    scopes=scopes
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
    
function handleMessage(event) {
    if (event.origin !== 'http://localhost:8000') {
        console.log('Invalid origin', event.origin);
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
}

function openLoginWindow() {
    window.removeEventListener('message', handleMessage);
    window.addEventListener('message', handleMessage);
    
    console.log('added event listener for message');
    
    const width = 500;
    const height = 600;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2.5;
    
    const popup = window.open(
        'http://localhost:8000/auth/login',
        'Google Login',
        `width=${width},height=${height},left=${left},top=${top}`
    );
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


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
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
        if user:
            return user
        raise HTTPException(status_code=401, detail='Invalid token or user not found')

@app.get("/auth/login")
async def login(response: Response):
    response.headers["Location"] = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&"
        f"client_id={os.getenv('GOOGLE_CLIENT_ID')}&"
        f"redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}&"
        f"scope={'%20'.join(scopes.keys())}&"
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
    token_info = token_response.json()
    token = token_info.get("access_token")

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
        if not user:
            try:
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    username=user_data['email'].split('@')[0],
                    name=user_data['name'],
                    picture=user_data.get('picture'),
                    google_token=token,
                    google_token_expires=token_info['expires_in'],
                    google_refresh_token=token_info.get('refresh_token'),
                )
            except KeyError as error:
                raise HTTPException(status_code=400, detail=f'KeyError: {error}')
            db_session.add(user)
            db_session.commit()
        else:
            user.google_token = token
            user.google_token_expires = token_info['expires_in']
            user.google_refresh_token = token_info.get('refresh_token')
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
@app.post('/chat', response_model=list[ChatMessage])
async def send_chat_message(
        incoming_chat_message: IncomingChatMessage,
        token: Annotated[str, Depends(oauth2_scheme)],
        current_user: User = Depends(get_current_user)
):
    ai_response = await get_ai_response(
        incoming_chat_message.message,
        token,
        current_user
    )

    with Session(engine) as db_session:
        chat_message_user = ChatMessage(
            user=current_user,
            message=incoming_chat_message.message,
            sender='user'
        )
        db_session.add(chat_message_user)

        chat_message_ai = ChatMessage(
            user=current_user,
            message=ai_response,
            sender='ai-assistant'
        )
        db_session.add(chat_message_ai)

        db_session.commit()

        return current_user.messages


@app.post('/delete-chat-message')
async def delete_chat_message(select_chat_message: SelectChatMessage, current_user: User = Depends(get_current_user)):
    with Session(engine) as db_session:
        statement = select(ChatMessage).where(ChatMessage.id == select_chat_message.message_id)
        try:
            chat_message = db_session.exec(statement).one()
        except NoResultFound:
            raise HTTPException(status_code=404, detail='Message not found')
        if chat_message.user_id != current_user.id:
            raise HTTPException(status_code=403, detail='Forbidden')
        db_session.delete(chat_message)
        db_session.commit()
        return {'status': 'success'}


@app.get('/chat')
async def get_chat_messages(current_user_dependency: User = Depends(get_current_user)):
    with Session(engine) as db_session:
        user_in_session = db_session.get(User, current_user_dependency.id)
        if not user_in_session:
            raise HTTPException(status_code=404, detail="User not found in current session")
        return user_in_session.messages


@app.delete('/clear-chat')
async def clear_chat(current_user_dependency: User = Depends(get_current_user)):
    with Session(engine) as db_session:
        user_in_session = db_session.get(User, current_user_dependency.id)
        if not user_in_session:
            raise HTTPException(status_code=404, detail="User not found in current session")
        user_in_session.messages = []
        db_session.commit()
        return {'status': 'success'}