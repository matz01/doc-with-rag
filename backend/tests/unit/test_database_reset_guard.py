"""Unit tests for the URL-safety guard of `reset_test_database()`.

`reset_test_database()` runs `DROP SCHEMA public CASCADE`, destructive SQL whose only
safe target is the dedicated test database. These tests pin the decision logic of
`is_safe_to_reset()`: the target must be a `*_test` database AND must not be the same
URL the live app uses. Pure URL logic: no database connection is opened here.
"""

from tests.integration._database import is_safe_to_reset

APP_URL = "postgresql://doc_user:secret@localhost:5432/docrag"


def test_returns_true_when_the_database_name_ends_with_test_and_the_url_differs_from_the_app_url():
    """A clearly test-named database on a different URL is safe to drop and rebuild."""
    target = "postgresql://doc_user:secret@db-server:5433/docrag_test"

    assert is_safe_to_reset(target, APP_URL) is True


def test_returns_false_when_the_target_database_is_not_a_test_database():
    """A database whose name does not end with `_test` must never be dropped."""
    target = "postgresql://doc_user:secret@db-server:5433/docrag_staging"

    assert is_safe_to_reset(target, APP_URL) is False


def test_returns_false_when_the_url_equals_the_app_url_even_if_the_name_ends_with_test():
    """The same URL as the app's DATABASE_URL is refused even with a `_test` name,
    so a developer can never drop the schema of the live app database."""
    target = "postgresql://doc_user:secret@localhost:5432/docrag_test"

    assert is_safe_to_reset(target, target) is False


def test_returns_true_when_only_the_database_name_matches_but_the_server_differs():
    """A `*_test` database on another server (different host, port, credentials) is
    still safe: only the full URL match with the app counts as a collision."""
    target = "postgresql://other_user:other@other-host:9999/docrag_test"

    assert is_safe_to_reset(target, APP_URL) is True
