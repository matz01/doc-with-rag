"""Shared helpers for the integration tests: which database to test against, and
making sure that database exists with pgvector.

Integration tests will insert and delete documents from phase 3 on, so they must
never run against the database the API serves. `TEST_DATABASE_URL` can point at a
completely different server; without it, the URL is derived by swapping the database
name of the app's `DATABASE_URL` to `docrag_test`, so server and credentials always
come from the same source the app itself uses.
"""

from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg import sql
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import REPO_ROOT_ENV_FILE

TEST_DATABASE_NAME = "docrag_test"


class _UrlSettings(BaseSettings):
    """Reads only the two database URLs, with the same .env and env-var precedence as
    `Settings`.

    A minimal class, not the full `Settings`: the URLs come from the same file the app
    uses, without invoking provider-key validation, which the tests replace with fakes
    anyway.
    """

    model_config = SettingsConfigDict(env_file=REPO_ROOT_ENV_FILE, extra="ignore")
    database_url: str = "postgresql://docrag:docrag@localhost:5432/docrag"
    test_database_url: str | None = None


def _test_database_url() -> str:
    """The exact URL the integration tests run against (never the app's database).

    `TEST_DATABASE_URL`, when set (environment or .env), is used as is: the developer
    takes responsibility for the target. Otherwise the app's URL is reused with only
    the database name swapped, so the tests always hit the dedicated test database.

    The pydantic-settings class already applies the precedence "environment variable
    wins over .env", so no separate os.environ check is needed.
    """
    explicit = _UrlSettings().test_database_url
    if explicit:
        return explicit
    parts = urlsplit(_UrlSettings().database_url)
    return urlunsplit(parts._replace(path=f"/{TEST_DATABASE_NAME}"))


def ensure_test_database() -> None:
    """Create the test database (with pgvector) if it does not exist yet.

    `infra/postgres/init.sql` only runs on a fresh data volume; this also covers
    existing volumes, including one created before the test database was introduced.
    Connects to the server's default `postgres` database with the same credentials as
    the final URL, so a working app connection implies a working fixture.
    """
    target = _test_database_url()
    # urlsplit handles a URL with query parameters; a key/value DSN is not supported
    # for TEST_DATABASE_URL (documented: the value must be a postgres:// URL).
    dbname = urlsplit(target).path.rpartition("/")[2]
    admin_url = urlunsplit(urlsplit(target)._replace(path="/postgres"))

    # autocommit from the start: CREATE DATABASE is refused inside a transaction block,
    # and psycopg opens an implicit transaction at the first execute().
    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            exists = cursor.fetchone() is not None
        if not exists:
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))

    with psycopg.connect(target) as conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
