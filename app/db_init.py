from pathlib import Path
from sqlalchemy import create_engine, text
from .config import Config

def init_db():
    engine = create_engine(Config().database_url)
    schema = Path(__file__).resolve().parent.parent / "schema.sql"
    statements = [s.strip() for s in schema.read_text(encoding="utf-8").split(";") if s.strip()]
    with engine.begin() as conn:
        for statement in statements: conn.execute(text(statement))

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
