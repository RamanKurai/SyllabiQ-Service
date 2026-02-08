import asyncpg
from sqlalchemy.engine import make_url
from app.config import settings
import asyncio


async def ensure_postgres_db_exists():
    """
    If DATABASE_URL points to a Postgres DB and AUTO_CREATE_DB is enabled,
    attempt to create the database and role (if missing) using DATABASE_SUPERUSER_URL.
    """
    db_url = settings.DATABASE_URL
    if not db_url.startswith("postgresql+asyncpg://"):
        return
    if not settings.AUTO_CREATE_DB:
        return

    # Parse target DB URL
    url = make_url(db_url)
    target_db = url.database
    target_user = url.username
    target_pass = url.password

    # Determine superuser/admin connection info
    super_url = settings.DATABASE_SUPERUSER_URL or db_url
    sup = make_url(super_url)
    sup_db = sup.database or "postgres"
    sup_user = sup.username
    sup_pass = sup.password
    sup_host = sup.host or "localhost"
    sup_port = sup.port or 5432

    # Build asyncpg connection string for the admin DB
    sup_conn = f"postgresql://{sup_user}:{sup_pass}@{sup_host}:{sup_port}/{sup_db}"

    print(f"[db.utils] Ensuring Postgres DB '{target_db}' exists (as owner '{target_user}')")
    try:
        conn = await asyncpg.connect(sup_conn)
    except Exception as e:
        print(f"[db.utils] Could not connect to superuser DB: {e}")
        return

    try:
        # Create role if missing
        role_exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = $1", target_user)
        if not role_exists:
            print(f"[db.utils] Creating role '{target_user}'")
            # Some utility statements do not accept parameter placeholders in all positions.
            # Safely embed the password literal after escaping single quotes.
            def _quote_literal(s: str) -> str:
                return s.replace("'", "''")

            pwd_clause = ""
            if target_pass:
                pwd_clause = f" PASSWORD '{_quote_literal(target_pass)}'"
            await conn.execute(f'CREATE ROLE "{target_user}" WITH LOGIN{pwd_clause}')

        # Create database if missing
        db_exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target_db)
        if not db_exists:
            print(f"[db.utils] Creating database '{target_db}' owned by '{target_user}'")
            # CREATE DATABASE cannot accept parameters for identifiers, quote safely.
            await conn.execute(f'CREATE DATABASE "{target_db}" OWNER "{target_user}"')
        else:
            print(f"[db.utils] Database '{target_db}' already exists")
    except Exception as e:
        print(f"[db.utils] Error ensuring database exists: {e}")
    finally:
        await conn.close()


def ensure_postgres_db_exists_sync():
    """Helper to run the async ensure function from sync contexts if needed."""
    return asyncio.run(ensure_postgres_db_exists())

