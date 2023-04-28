import json
import os
import sys
sys.path.append('.')

import tempfile
import pytest

from modules.web_app.app import app, load_infos, save_infos

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_status(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200


def test_map(client):
    response = client.get('/map')
    assert response.status_code == 200


