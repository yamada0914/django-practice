"""
決済関連のビューのテスト
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings
from django.conf import settings
from django.urls import reverse
from base.models import Order, Card


@pytest.mark.django_db
def test_pay_with_stripe_requires_profile(authenticated_client, user_with_profile, published_card):
    """プロフィールが未入力の場合、プロフィールページにリダイレクトされる"""
    # プロフィールを空にする
    profile = user_with_profile.profile
    profile.name = ''
    profile.save()

    # カートに商品を追加
    session = authenticated_client.session
    session['cart'] = {
        'items': {published_card.pk: 1},
        'total': published_card.price
    }
    session.save()

    response = authenticated_client.post('/pay/checkout/')
    assert response.status_code == 302
    assert response.url == '/profile/'


@pytest.mark.django_db
def test_pay_with_stripe_requires_cart(authenticated_client, user_with_profile):
    """カートが空の場合、トップページにリダイレクトされる"""
    response = authenticated_client.post('/pay/checkout/')
    assert response.status_code == 302
    assert response.url == '/'


@pytest.mark.django_db
def test_pay_with_stripe_insufficient_stock(authenticated_client, user_with_profile, published_card):
    """在庫不足の場合、カートページにリダイレクトされる"""
    # カートに在庫を超える数量を追加
    session = authenticated_client.session
    session['cart'] = {
        'items': {published_card.pk: 10},
        'total': published_card.price * 10
    }
    session.save()

    response = authenticated_client.post('/pay/checkout/')
    assert response.status_code == 302
    assert response.url == '/cart/'


@pytest.mark.django_db
@override_settings(
    STRIPE_TAX_RATE_ID='tax_rate_test',
    TAX_RATE=settings.TAX_RATE,
    MY_URL='http://testserver'
)
@patch('base.views.pay.stripe.checkout.Session.create')
def test_pay_with_stripe_success(mock_stripe_create, authenticated_client, user_with_profile, published_card):
    """正常な決済処理が動作することを確認"""
    # Stripe のモック設定
    mock_checkout_session = MagicMock()
    mock_checkout_session.url = 'https://checkout.stripe.com/test'
    mock_stripe_create.return_value = mock_checkout_session

    # カートに商品を追加
    session = authenticated_client.session
    session['cart'] = {
        'items': {published_card.pk: 2},
        'total': published_card.price * 2
    }
    session.save()

    # 在庫数を記録
    initial_stock = published_card.stock
    initial_sold_count = published_card.sold_count

    response = authenticated_client.post('/pay/checkout/')

    # リダイレクトされることを確認
    assert response.status_code == 302
    assert response.url == 'https://checkout.stripe.com/test'

    # 注文が作成されたことを確認
    order = Order.objects.filter(user=user_with_profile).first()
    assert order is not None
    assert order.is_confirmed is False
    assert order.amount == published_card.price * 2
    assert len(order.items) == 1
    assert order.items[0]['pk'] == published_card.pk
    assert order.items[0]['quantity'] == 2

    # 配送先情報が保存されていることを確認
    assert order.shipping['name'] == user_with_profile.profile.name
    assert order.shipping['zipcode'] == user_with_profile.profile.zipcode

    # 在庫と販売数が更新されたことを確認
    published_card.refresh_from_db()
    assert published_card.stock == initial_stock - 2
    assert published_card.sold_count == initial_sold_count + 2

    # Stripe セッションが作成されたことを確認
    mock_stripe_create.assert_called_once()


@pytest.mark.django_db
@override_settings(
    STRIPE_TAX_RATE_ID='tax_rate_test',
    TAX_RATE=settings.TAX_RATE,
    MY_URL='http://testserver'
)
@patch('base.views.pay.stripe.checkout.Session.create')
def test_pay_with_stripe_creates_order_with_shipping(mock_stripe_create, authenticated_client, user_with_profile, published_card):
    """注文に配送先情報が正しく保存されることを確認"""
    mock_checkout_session = MagicMock()
    mock_checkout_session.url = 'https://checkout.stripe.com/test'
    mock_stripe_create.return_value = mock_checkout_session

    session = authenticated_client.session
    session['cart'] = {
        'items': {published_card.pk: 1},
        'total': published_card.price
    }
    session.save()

    authenticated_client.post('/pay/checkout/')

    order = Order.objects.filter(user=user_with_profile).first()
    assert order is not None
    assert order.shipping['name'] == 'テスト ユーザー'
    assert order.shipping['zipcode'] == '1000001'
    assert order.shipping['prefecture'] == '東京都'
    assert order.shipping['city'] == '千代田区'
    assert order.shipping['address1'] == '千代田1-1-1'
    assert order.shipping['tel'] == '09012345678'


@pytest.mark.django_db
def test_pay_success_view_missing_order_id(authenticated_client):
    """注文 ID が指定されていない場合、注文一覧にリダイレクトされる"""
    response = authenticated_client.get('/pay/success/')
    assert response.status_code == 302
    assert response.url == '/pages/orders-history/'


@pytest.mark.django_db
def test_pay_success_view_invalid_order_id(authenticated_client, user_with_profile):
    """存在しない注文IDの場合、注文一覧にリダイレクトされる"""
    response = authenticated_client.get('/pay/success/?order_id=invalid_id')
    assert response.status_code == 302
    assert response.url == '/pages/orders-history/'


@pytest.mark.django_db
def test_pay_success_view_already_confirmed(authenticated_client, user_with_profile, published_card):
    """既に確定済みの注文の場合、注文一覧にリダイレクトされる"""
    # 注文を作成して確定済みにする
    order = Order.objects.create(
        user=user_with_profile,
        uid=str(user_with_profile.pk),
        items=[{'pk': published_card.pk,
                'name': published_card.name, 'quantity': 1}],
        shipping={'name': 'test'},
        amount=500,
        tax_included=550,
        is_confirmed=True
    )

    response = authenticated_client.get(f'/pay/success/?order_id={order.pk}')
    assert response.status_code == 302
    assert response.url == '/pages/orders-history/'


@pytest.mark.django_db
def test_pay_success_view_confirms_order(authenticated_client, user_with_profile, published_card):
    """正常な決済成功処理が動作することを確認"""
    # 注文を作成
    order = Order.objects.create(
        user=user_with_profile,
        uid=str(user_with_profile.pk),
        items=[{'pk': published_card.pk,
                'name': published_card.name, 'quantity': 1}],
        shipping={'name': 'test'},
        amount=500,
        tax_included=550,
        is_confirmed=False
    )

    # カートに商品を追加（クリアされることを確認するため）
    session = authenticated_client.session
    session['cart'] = {
        'items': {published_card.pk: 1},
        'total': 500
    }
    session.save()

    response = authenticated_client.get(f'/pay/success/?order_id={order.pk}')

    # 注文が確定されたことを確認
    order.refresh_from_db()
    assert order.is_confirmed is True

    # カートがクリアされたことを確認
    session = authenticated_client.session
    assert 'cart' not in session or not session.get('cart', {}).get('items')


@pytest.mark.django_db
def test_pay_cancel_view_restores_stock(authenticated_client, user_with_profile, published_card):
    """決済キャンセル時に在庫が復元されることを確認"""
    # 注文を作成（在庫を減らした状態をシミュレート）
    published_card.stock = 3
    published_card.sold_count = 2
    published_card.save()

    order = Order.objects.create(
        user=user_with_profile,
        uid=str(user_with_profile.pk),
        items=[{
            'pk': published_card.pk,
            'name': published_card.name,
            'quantity': 2
        }],
        shipping={'name': 'test'},
        amount=1000,
        tax_included=1100,
        is_confirmed=False
    )

    response = authenticated_client.get('/pay/cancel/')

    # 在庫が復元されたことを確認
    published_card.refresh_from_db()
    assert published_card.stock == 5  # 3 + 2 = 5
    assert published_card.sold_count == 0  # 2 - 2 = 0

    # 未確定注文が削除されたことを確認
    assert not Order.objects.filter(
        user=user_with_profile, is_confirmed=False).exists()


@pytest.mark.django_db
def test_pay_cancel_view_deletes_unconfirmed_orders(authenticated_client, user_with_profile, published_card):
    """決済キャンセル時に未確定注文が削除されることを確認"""
    # 在庫と販売数を設定
    published_card.stock = 2  # 5 - 3 = 2
    published_card.sold_count = 3  # 3 個販売済み
    published_card.save()

    # 複数の未確定注文を作成
    for i in range(3):
        Order.objects.create(
            user=user_with_profile,
            uid=str(user_with_profile.pk),
            items=[{'pk': published_card.pk,
                    'name': published_card.name, 'quantity': 1}],
            shipping={'name': 'test'},
            amount=500,
            tax_included=550,
            is_confirmed=False
        )

    # 確定済みの注文も作成
    confirmed_order = Order.objects.create(
        user=user_with_profile,
        uid=str(user_with_profile.pk),
        items=[{'pk': published_card.pk,
                'name': published_card.name, 'quantity': 1}],
        shipping={'name': 'test'},
        amount=500,
        tax_included=550,
        is_confirmed=True
    )

    response = authenticated_client.get('/pay/cancel/')

    # 未確定注文のみが削除されたことを確認
    assert Order.objects.filter(
        user=user_with_profile, is_confirmed=False).count() == 0
    assert Order.objects.filter(pk=confirmed_order.pk).exists()  # 確定済みは残る
