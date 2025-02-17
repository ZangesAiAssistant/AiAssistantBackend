import os
import secrets

import dotenv
from flask import Flask, url_for, redirect, session
from authlib.jose import jwt
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from database.core import alembic, db, run_migrations
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
    # access_token_url="https://oauth2.googleapis.com/token",
    # authorize_url="https://accounts.google.com/o/oauth2/auth",
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
        return f"Hello, {current_user.name}! <a href='/logout'>Logout</a>"
    return "Welcome! <a href='/login'>Login</a>"

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