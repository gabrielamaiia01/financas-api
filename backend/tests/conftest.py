import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client(tmp_path, monkeypatch):
    import models

    monkeypatch.setattr(models, "DATABASE_PATH", str(tmp_path / "financas.db"))
    models.inicializar_banco()

    from app import app

    return app.test_client()
