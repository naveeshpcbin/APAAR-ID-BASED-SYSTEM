import pytest
from sqlalchemy import create_engine
from app.core.database import sanitize_db_url

def test_sanitize_sqlite_unchanged():
    sqlite_url = "sqlite:///./pramaan.db"
    assert sanitize_db_url(sqlite_url) == sqlite_url

def test_sanitize_postgres_scheme_and_driver_selection():
    raw_url = "postgres://postgres:mysecretpass@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    sanitized = sanitize_db_url(raw_url)
    
    # Must normalize 'postgres://' to 'postgresql://' or 'postgresql+psycopg2://'
    assert sanitized.startswith("postgresql")
    assert "postgres:mysecretpass" in sanitized
    assert "aws-0-ap-south-1.pooler.supabase.com:6543/postgres" in sanitized

def test_sanitize_password_brackets_stripped():
    raw_url = "postgresql://postgres:[Naveeapaarid@26]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    sanitized = sanitize_db_url(raw_url)
    
    # Bracket [ ] should be stripped, and special char @ URL-encoded
    assert "[" not in sanitized
    assert "]" not in sanitized
    assert "Naveeapaarid%4026" in sanitized

def test_sanitize_special_chars_url_encoded():
    raw_url = "postgresql://user:pass#123@localhost:5432/testdb"
    sanitized = sanitize_db_url(raw_url)
    # '#' should be percent-encoded to %23
    assert "#" not in sanitized.split("@")[0]
    assert "pass%23123" in sanitized

def test_sanitize_host_brackets_stripped():
    raw_url = "postgresql://user:pass@aws-0-[ap-southeast-2].pooler.supabase.com:6543/postgres"
    sanitized = sanitize_db_url(raw_url)
    assert "[" not in sanitized
    assert "]" not in sanitized
    assert "@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres" in sanitized

def test_postgresql_driver_engine_instantiation():
    # Verify SQLAlchemy can successfully instantiate the engine with the sanitized URL without ImportError
    simulated_url = "postgresql+psycopg2://mock_user:mock_pass@127.0.0.1:5432/mock_db"
    engine = create_engine(simulated_url)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "psycopg2"
