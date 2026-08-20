import pytest

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'FoodSaver' in response.data


def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Welcome back' in response.data


def test_register_page_loads(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Create your account' in response.data


def test_delete_food_route_works(client):
    client.post('/login', data={'username': 'demo', 'password': 'demo123'}, follow_redirects=True)
    response = client.post('/delete_food/1', follow_redirects=True)
    assert response.status_code == 200
