import urllib.parse
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

def sanitize_db_url(raw_url: str) -> str:
    """
    Robustly sanitizes PostgreSQL / Supabase connection strings:
    - Strips surrounding brackets like [password] or [Naveeapaarid@26]
    - URL-encodes special characters in passwords (e.g. '@', '#', '%')
    - Normalizes postgres:// to postgresql://
    - Enforces explicit driver dialect (psycopg2 fallback) to prevent SQLAlchemy 2.1+ ModuleNotFoundError: No module named 'psycopg'
    """
    if not raw_url or raw_url.startswith("sqlite"):
        return raw_url
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    
    if "://" in raw_url and "@" in raw_url:
        scheme, rest = raw_url.split("://", 1)
        user_pass, host_part = rest.rsplit("@", 1)
        if ":" in user_pass:
            username, password = user_pass.split(":", 1)
            if password.startswith("[") and password.endswith("]"):
                password = password[1:-1]
            # Avoid double-encoding if already encoded
            if "%" not in password:
                password = urllib.parse.quote_plus(password)
            
            # Ensure safe driver selection if generic postgresql:// was provided
            if scheme == "postgresql":
                try:
                    import psycopg  # noqa: F401
                except ImportError:
                    try:
                        import psycopg2  # noqa: F401
                        scheme = "postgresql+psycopg2"
                    except ImportError:
                        pass
            # Clean any accidental brackets in host_part (e.g. aws-0-[ap-southeast-2].pooler.supabase.com)
        if "[" in host_part or "]" in host_part:
            host_part = host_part.replace("[", "").replace("]", "")

        return f"{scheme}://{username}:{password}@{host_part}"
    return raw_url

# Select database URL: prioritize SUPABASE_DATABASE_URL if provided, else fallback to DATABASE_URL
raw_db_url = sanitize_db_url(settings.SUPABASE_DATABASE_URL or settings.DATABASE_URL)

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if raw_db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs["connect_args"] = connect_args
else:
    # PostgreSQL / Supabase configuration
    if "sslmode=" not in raw_db_url and ("supabase.co" in raw_db_url or "supabase.com" in raw_db_url or "pooler" in raw_db_url):
        connect_args["sslmode"] = "require"
    engine_kwargs["connect_args"] = connect_args
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    raw_db_url,
    **engine_kwargs
)

if raw_db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
