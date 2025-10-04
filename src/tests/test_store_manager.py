"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # 1. Créez un article (`POST /products`) assumant que l'utilisateur avec user_id=1 existe déjà
    product_data = {'name': 'Some Item', 'sku': '12345', 'price': 99.90}
    response = client.post('/products',
                          data=json.dumps(product_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['product_id'] > 0 
    product_id = data['product_id']

    # 2. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    stock_data = {'product_id': product_id, 'quantity': 5}
    stock_response = client.post('/stocks',
                                data=json.dumps(stock_data),
                                content_type='application/json')
    assert stock_response.status_code == 201

    # 3. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    stock_check_response = client.get(f'/stocks/{product_id}')
    assert stock_check_response.status_code == 201
    stock_data = stock_check_response.get_json()
    assert stock_data['quantity'] == 5

    # 4. Faites une commande de l'article que vous avez crée, 2 unités (`POST /orders`)
    order_data = {
        'user_id': 1,
        'items': [
            {
                'product_id': product_id,
                'quantity': 2
            }
        ]
    }
    order_response = client.post('/orders',
                                data=json.dumps(order_data),
                                content_type='application/json')
    assert order_response.status_code == 201
    order_data = order_response.get_json()
    order_id = order_data['order_id']

    # 5. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    stock_after_order_response = client.get(f'/stocks/{product_id}')
    assert stock_after_order_response.status_code == 201
    stock_after_order_data = stock_after_order_response.get_json()
    assert stock_after_order_data['quantity'] == 3

    # 6. Étape extra: supprimez la commande et vérifiez le stock de nouveau. Le stock devrait augmenter après la suppression de la commande.
    delete_order_response = client.delete(f'/orders/{order_id}')
    assert delete_order_response.status_code == 200
    delete_data = delete_order_response.get_json()
    assert delete_data['deleted'] == True
    final_stock_response = client.get(f'/stocks/{product_id}')
    assert final_stock_response.status_code == 201
    final_stock_data = final_stock_response.get_json()
    assert final_stock_data['quantity'] == 5