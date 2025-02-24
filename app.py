import os
import secrets

import dotenv
from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for, redirect, session, request, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from ai_integration import get_ai_response
from database.core import alembic, db
from database.models.chat import Chat
from database.models.chat_message import ChatMessage
from database.models.user import User
from flask_config import apply_config

dotenv.load_dotenv()

app = Flask(__name__)
apply_config(app)

db.init_app(app)
alembic.init_app(app)

oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# run_migrations(app)


# Load user from database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/")
def home():
    if current_user.is_authenticated:
        messages = []
        if current_user.chats is not None:
            messages = current_user.chats[0].messages
        return render_template("home_authenticated.html", user=current_user, messages=messages)
    return render_template("home_unauthenticated.html")

@app.route("/login")
def login():
    nonce = secrets.token_urlsafe(16)  # Generate a secure nonce
    session["nonce"] = nonce  # Store nonce in session
    return oauth.google.authorize_redirect(
        url_for("authorize", _external=True),
        nonce=nonce  # Pass nonce to Google
    )

@app.route("/login/callback")
def authorize():
    token = oauth.google.authorize_access_token()
    nonce = session.pop("nonce", None)

    if not nonce:
        return "Nonce missing. Authentication failed.", 400

    user_info = oauth.google.parse_id_token(token, nonce=nonce)

    # Check if user exists
    user = User.query.filter_by(id=user_info["sub"]).first()

    # Create new user if not exists
    if not user:
        user = User(
            id=user_info["sub"],
            email=user_info["email"],
            username=user_info["email"].split("@")[0],
            name=user_info["name"],
            picture=user_info["picture"],
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/chat-message", methods=["POST"])
@login_required
def post_chat_message():
    message = request.form["message"]
    user: User = current_user

    # get the first chat or create a new one
    chat = user.chats[0] if user.chats else Chat(user=user)
    db.session.add(chat)
    db.session.commit() # TODO: Check if this is necessary

    # create a new chat message
    chat_message_user = ChatMessage(chat=chat, message=message, sender="user")
    db.session.add(chat_message_user)

    # get a response from the AI and create a new chat message
    chat_message_ai = ChatMessage(chat=chat, message=get_ai_response(message), sender="ai_assistant")
    db.session.add(chat_message_ai)

    # commit the messages to the database
    db.session.commit()

    return redirect(url_for("home"))

@app.route("/delete-chat-message", methods=["POST"])
@login_required
def delete_chat_message():
    message_id = request.form["message_id"]
    message = ChatMessage.query.get(message_id)
    if message is None:
        return redirect(url_for("home"))
    if message.chat.user_id != current_user.id:
        return redirect(url_for("home")) # TODO: Add error message
    db.session.delete(message)
    db.session.commit()

    return redirect(url_for("home"))