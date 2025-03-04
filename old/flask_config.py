import os

from sqlalchemy import URL


def apply_config(app):
    # Flask-SQLAlchemy
    database_type = os.environ.get('DATABASE_TYPE', 'sqlite')
    if database_type == 'postgresql':
        if os.environ.get('DATABASE_IP') is None:
            raise ValueError('DATABASE_IP must be set when using postgres')
        if os.environ.get('DATABASE_NAME') is None:
            raise ValueError('DATABASE_NAME must be set when using postgres')
        if os.environ.get('DATABASE_USER') is None:
            raise ValueError('DATABASE_USER must be set when using postgres')
        if os.environ.get('DATABASE_PASSWORD') is None:
            raise ValueError('DATABASE_PASSWORD must be set when using postgres')

        url_object = URL.create(
            drivername='postgresql+psycopg2',
            username=os.environ.get('DATABASE_USER'),
            password=os.environ.get('DATABASE_PASSWORD'),
            host=os.environ.get('DATABASE_IP'),
            port=os.environ.get('DATABASE_PORT', 5432),
            database=os.environ.get('DATABASE_NAME')
        )
        app.config['SQLALCHEMY_DATABASE_URI'] = url_object

    elif database_type == 'sqlite':
        database_path = f'data/{os.environ.get('DATABASE_NAME', 'db')}.sqlite3'
        if not os.path.exists(os.path.dirname(database_path)):
            os.makedirs(os.path.dirname(database_path))
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Flask-Alembic
    app.config['ALEMBIC'] = {
        'script_location': 'database/migrations',
    }

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")