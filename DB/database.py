import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

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

def apply_auto_migrations(db_engine):
    """Automatycznie uzupełnia brakujące kolumny w istniejących tabelach."""
    statements = [
        "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS solution TEXT;",
        "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tags VARCHAR(255) DEFAULT 'łatwe';",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'cpp';",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS language_id INTEGER DEFAULT 54;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS semester INTEGER DEFAULT 1;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS start_year INTEGER DEFAULT 2026;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS major VARCHAR(50) DEFAULT 'mechatro';",
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'submission_test_results_test_case_id_fkey'
            ) THEN
                ALTER TABLE submission_test_results DROP CONSTRAINT submission_test_results_test_case_id_fkey;
                ALTER TABLE submission_test_results ADD CONSTRAINT submission_test_results_test_case_id_fkey
                    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE;
            END IF;
        END $$;
        """,
    ]
    try:
        with db_engine.begin() as conn:
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass
    except Exception as e:
        logger.warning("Auto-migracja schematu bazy danych została pominięta: %s", e)

# 5. Dependency - funkcja pomocnicza do FastAPI, która bezpiecznie otwiera i zamyka sesję
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
