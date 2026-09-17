import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app import app

def test_healthz():
    client = app.test_client()
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_index_get():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200

def test_index_post():
    client = app.test_client()
    response = client.post('/', data={'name': 'Brandon'})
    assert response.status_code == 200
    assert b'Hello, Brandon' in response.data