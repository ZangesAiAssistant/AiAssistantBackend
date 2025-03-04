import os
from dotenv import load_dotenv
from sqlalchemy.exc import NoResultFound


load_dotenv()
# THIS NEEDS TO BE EXECUTED BEFORE ANY OTHER IMPORTS

import json

from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from contextlib import asynccontextmanager
from sqlmodel import select, Session
from fastapi import FastAPI, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

from .database import create_tables, engine
from .ai_integration import get_ai_response
# MUST IMPORT ALL MODELS, OTHERWISE RELATIONSHIPS WILL NOT WORK # TODO: find a better way to do this
from .models.incoming_chat_message import IncomingChatMessage
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
    current_session_user = request.session.get('user')
    if current_session_user:
        with Session(engine) as db_session:
            statement = select(User).where(User.id == current_session_user['id'])
            user = db_session.exec(statement).first()
            chat_messages_html = '\n'.join([
                f'<li>{chat_message.sender}: {chat_message.message} <form action="/delete-chat-message" method="post"><input type="hidden" name="message_id" value="{chat_message.id}"><button type="submit">Delete</button></form></li>'
                for chat_message in user.chats[0].messages
            ])
            html = (
                '<h1>Logged in</h1>'
                f'<p>{user.username}</p>'
                f'<a href="{request.url_for("logout")}">logout</a>'
                '<h2>Chat</h2>'
                '<ul>'
                f'{chat_messages_html}'
                '</ul>'
                f'<form action="{request.url_for("send_chat_message")}" method="post">'
                '<input type="text" name="message" required>'
                '<button type="submit">Send</button>'
                '</form>'
            )
            return HTMLResponse(html)
    return HTMLResponse(f'<a href="{request.url_for("login")}">login</a>')

@app.post('/chat')
async def send_chat_message(request: Request, message: str = Form(...)):
                            # incoming_chat_message: IncomingChatMessage):
    current_session_user = request.session.get('user')
    if not current_session_user:
        raise HTTPException(status_code=401, detail='Unauthorized')

    with Session(engine) as db_session:
        statement = select(User).where(User.id == current_session_user['id'])
        user = db_session.exec(statement).first()
        chat = user.chats[0]

        # get the most recent messages
        statement = select(ChatMessage).where(ChatMessage.chat_id == chat.id).order_by(ChatMessage.send_time.desc()).limit(5).where()
        recent_messages = db_session.exec(statement).all()
        recent_messages_str = '\n'.join([
            f'{message.sender}@{message.send_time}: {message.message}'
            for message in recent_messages
        ])
        ai_response = await get_ai_response(message, recent_messages_str)

        chat_message_user = ChatMessage(
            chat=chat,
            message=message,
            sender='user'
        )
        db_session.add(chat_message_user)

        chat_message_ai = ChatMessage(
            chat=chat,
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
    with Session(engine) as db_session:
        statement = select(User).where(User.id == user_data['sub'])
        user = db_session.exec(statement).first()
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
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
    request.session['user'] = user.model_dump()

    return RedirectResponse(url=request.url_for('homepage'))

@app.get('/auth/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url=request.url_for('homepage'))