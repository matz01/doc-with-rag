"""Shared fixtures for the integration tests.

They run against the dedicated test database (`docrag_test`, never the app's
database); this fixture creates that database with pgvector when it is missing,
covering docker volumes created before the test database was introduced.
"""

import pytest

from ._database import ensure_test_database


@pytest.fixture(autouse=True, scope="session")
def dedicated_test_database():
    ensure_test_database()
