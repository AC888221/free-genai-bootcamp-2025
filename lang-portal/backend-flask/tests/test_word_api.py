# Jiantizi adaption for Bootcamp Week 1:
# Test word API with Chinese characters

import pytest
from app import create_app
import json

@pytest.fixture(scope='function')
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'DATABASE': ':memory:'
    })
    return app

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    with app.test_client() as test_client:
        with app.app_context():
            yield test_client

def test_create_word(client):
    response = client.post('/api/words', json={
        'jiantizi': '你好',
        'pinyin': 'nǐ hǎo',
        'english': 'hello'
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Test route'

def test_get_word(client):
    response = client.get('/api/words/1')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Test route' 