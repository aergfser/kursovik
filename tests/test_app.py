import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_filter_details(client):
    with client.session_transaction() as sess:
        sess['user_id'] = '67e25f21f4f42e28e7d30f2f'

    response = client.get('/details?DCONMS_min=100')
    assert response.status_code == 200

    html = response.data.decode('utf-8')
    assert 'PICCO R-MFT60 6-4 L12' in html

def test_download_word(client):
    with client.session_transaction() as sess:
        sess['user_id'] = '67e25f21f4f42e28e7d30f2f'

    response = client.post('/download_word', 
                         json={'id_tool': '671e1664844277f06ee0bcca'})
    assert response.status_code == 200
    assert 'application/vnd.openxmlformats' in response.headers['Content-Type']