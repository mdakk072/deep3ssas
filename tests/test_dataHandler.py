import json
import os
import sys
sys.path.append('.')
import tempfile
import base64
import pytest
from modules.data_handler.dataHandler import app, load_infos, save_infos

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_parking_structure(client):
    response = client.get('/parking_structure')
    assert response.status_code == 200
    assert isinstance(json.loads(response.data), dict)

def test_get_status(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    assert isinstance(json.loads(response.data), dict)


def test_update_current_parking_id(client):
    data = {"current_parking_id": "2"}

    response = client.post('/currentID', json=data)
    assert response.status_code == 200
    assert json.loads(response.data)["status"] == "success"
