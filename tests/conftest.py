import pytest

from app.main import app
from app.database import get_db


@pytest.fixture(autouse=True)
def isolate_app_database(request):
    """
    Ensure each test module uses its own database
    and dependency override.

    Each existing test file already defines:
        - TestingSessionLocal
        - override_get_db

    When pytest loads multiple test modules, their global
    dependency overrides can overwrite each other.

    This fixture restores the correct override for the
    currently running test module.
    """

    test_module = request.module

    module_override = getattr(
        test_module,
        "override_get_db",
        None,
    )

    if module_override is not None:
        app.dependency_overrides[get_db] = module_override

    yield

    # Keep the application clean after every test.
    app.dependency_overrides.pop(get_db, None)