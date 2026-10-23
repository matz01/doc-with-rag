"""Plain-SQL schema migrations, applied in order and tracked in `schema_migrations`.

The migration files live in `app/db/migrations/` as numbered `.sql` files (see the
python-backend skill: the schema and the permission filter stay explicit, no ORM).
Each pending file runs in its own transaction together with its `schema_migrations`
row, so a migration is either fully applied or not at all.
"""

from pathlib import Path

import psycopg

MIGRATIONS_DIRECTORY = Path(__file__).parent / "migrations"


def apply_migrations(database_url: str) -> None:
    """Apply every pending migration file, in filename order."""
    with psycopg.connect(database_url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename text PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT filename FROM schema_migrations")
            applied = {row[0] for row in cursor.fetchall()}

        for path in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
            if path.name in applied:
                continue
            # Each file runs in its own transaction together with its tracking row, so
            # a migration is either fully applied or not at all.
            with conn.transaction():
                conn.execute(path.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))
