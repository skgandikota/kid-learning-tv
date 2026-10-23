import re

import pytest

from app.main import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "SECRET_KEY": "test-secret", "DATA_DIR": tmp_path})


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_for(client):
    page = client.get("/parent").get_data(as_text=True)
    return re.search(r'<meta name="csrf-token" content="([^"]+)"', page).group(1)
