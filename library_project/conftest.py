import pytest
from library import Library


@pytest.fixture
def db_lib(tmp_path):
    """Create a temporary sqlite database file and yield a Library connected to it."""
    db_file = tmp_path / "test_library.db"
    lib = Library(db_path=str(db_file))
    yield lib
    try:
        lib.close()
    except Exception:
        pass


@pytest.fixture
def empty_lib(db_lib):
    """Alias for an empty DB-backed library (keeps existing tests unchanged)."""
    return db_lib


@pytest.fixture
def lib_with_one_book(db_lib):
    db_lib.add_book("Python Basics", "Alice Author", "编程")
    return db_lib
