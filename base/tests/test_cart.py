import pytest


@pytest.mark.django_db
def test_add_to_cart(client, published_card):
    """カートに商品を追加できることを確認"""
    response = client.post(
        '/cart/add/',
        {
            'item_pk': published_card.pk,
            'quantity': 2,
        }
    )
    assert response.status_code == 302  # リダイレクト
    assert response.url == '/cart/'

    # セッションにカートが保存されているか確認
    cart = client.session.get('cart')
    assert cart is not None
    assert published_card.pk in cart['items']
    assert cart['items'][published_card.pk] == 2


@pytest.mark.django_db
def test_cart_list_view_shows_added_items(client, published_card):
    """カート一覧に追加した商品が表示されることを確認"""
    # カートに追加
    client.post('/cart/add/', {'item_pk': published_card.pk, 'quantity': 1})

    # カート一覧を表示
    response = client.get('/cart/')
    assert response.status_code == 200

    # カートに商品が含まれているか確認
    cart_items = list(response.context['object_list'])
    assert len(cart_items) == 1
    assert cart_items[0].pk == published_card.pk
    assert cart_items[0].quantity == 1


@pytest.mark.django_db
def test_cart_calculates_total_correctly(client, published_card):
    """カートの合計金額が正しく計算されることを確認"""
    # カートに追加（価格500円 × 数量2 = 1000円）
    client.post('/cart/add/', {'item_pk': published_card.pk, 'quantity': 2})

    response = client.get('/cart/')
    assert response.status_code == 200
    assert response.context['total'] == 1000


@pytest.mark.django_db
def test_cart_increase_quantity(client, published_card):
    """カート内の商品数量を増やせることを確認"""
    # 最初に1個追加
    client.post('/cart/add/', {'item_pk': published_card.pk, 'quantity': 1})

    # 数量を増やす
    response = client.post(
        '/cart/add/',
        {
            'item_pk': published_card.pk,
            'operation': 'increase',
            'max_stock': published_card.stock,
        }
    )
    assert response.status_code == 302

    # セッションで数量が2になっているか確認
    cart = client.session.get('cart')
    assert cart['items'][published_card.pk] == 2


@pytest.mark.django_db
def test_cart_decrease_quantity(client, published_card):
    """カート内の商品数量を減らせることを確認"""
    # 最初に2個追加
    client.post('/cart/add/', {'item_pk': published_card.pk, 'quantity': 2})

    # 数量を減らす
    response = client.post(
        '/cart/add/',
        {
            'item_pk': published_card.pk,
            'operation': 'decrease',
        }
    )
    assert response.status_code == 302

    # セッションで数量が1になっているか確認
    cart = client.session.get('cart')
    assert cart['items'][published_card.pk] == 1


@pytest.mark.django_db
def test_cart_remove_item(client, published_card):
    """カートから商品を削除できることを確認"""
    # カートに追加
    client.post('/cart/add/', {'item_pk': published_card.pk, 'quantity': 1})

    # 削除
    response = client.post(f'/cart/remove/{published_card.pk}/')
    assert response.status_code == 302
    assert response.url == '/cart/'

    # セッションから削除されているか確認
    cart = client.session.get('cart')
    assert cart is None or published_card.pk not in cart.get('items', {})


@pytest.mark.django_db
def test_cart_empty_view(client):
    """空のカートを表示できることを確認"""
    response = client.get('/cart/')
    assert response.status_code == 200
    assert len(response.context['object_list']) == 0
    assert response.context['total'] == 0


@pytest.mark.django_db
def test_cart_quantity_does_not_exceed_stock(client, published_card):
    """在庫を超えた数量を追加できないことを確認"""
    # published_card の在庫は5
    # 在庫を超える数量を増やそうとする
    client.post('/cart/add/', {'item_pk': published_card.pk, 'quantity': 3})

    # 在庫を超えるまで増やす
    for _ in range(5):  # 3 + 5 = 8 になるが、在庫は5なので5で止まる
        client.post(
            '/cart/add/',
            {
                'item_pk': published_card.pk,
                'operation': 'increase',
                'max_stock': published_card.stock,
            }
        )

    # 在庫を超えないことを確認
    cart = client.session.get('cart')
    assert cart['items'][published_card.pk] == published_card.stock  # 5で止まる
