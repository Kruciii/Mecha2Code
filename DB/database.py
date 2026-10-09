import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()
# 1. Connection String - adres Twojej bazy 
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("Brak zmiennej DATABASE_URL w pliku .env!")

# 2. Silnik (Engine) - to on zarządza faktycznym połączeniem z bazą
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Fabryka sesji - sesja to Twoje "okno" do wysyłania zapytań SQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Klasa bazowa - od niej będą dziedziczyć wszystkie Twoje tabele (np. User, Commit)
Base = declarative_base()

# 5. Dependency - funkcja pomocnicza do FastAPI, która bezpiecznie otwiera i zamyka sesję
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()