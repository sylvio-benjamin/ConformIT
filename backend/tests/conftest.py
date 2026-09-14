import pytest


@pytest.fixture(autouse=True)
def reset_storage_facade():
    from app.storage import reset_facade

    reset_facade()
    yield
    reset_facade()
