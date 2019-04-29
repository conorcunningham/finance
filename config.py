from tempfile import mkdtemp
from helpers import usd


class Config:

    # Ensure templates are auto-reloaded
    TEMPLATES_AUTO_RELOAD = True

    # Configure session to use filesystem (instead of signed cookies)
    SESSION_FILE_DIR = mkdtemp()
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

    # Tell Flask what SQLAlchemy database to use.
    SQLALCHEMY_DATABASE_URI = "sqlite:///finance.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

