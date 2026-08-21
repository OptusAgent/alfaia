import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_app_inicia_e_para_com_followup_worker_em_background():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
