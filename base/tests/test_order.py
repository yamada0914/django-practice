"""
注文関連のビューのテスト
"""
import pytest
from base.models import Order, Card
from django.utils import timezone


@pytest.mark.django_db
def test_order_index_view_requires_login(client):
    """注文一覧ページはログインが必要"""
    response = client.get('/orders/')
    assert response.status_code == 302  # ログインページにリダイレクト


@pytest.mark.django_db
def test_order_index_view_empty(authenticated_client, user_with_profile):
    """注文がない場合の一覧表示を確認"""
    response = authenticated_client.get('/orders/')
    assert response.status_code == 200
    assert len(response.context['object_list']) == 0


@pytest.mark.django_db
def test_order_index_view_shows_user_orders(authenticated_client, user_with_profile, published_card):
    """ユーザーの注文のみが表示されることを確認"""
    # 注文を作成
    order1 = Order.objects.create(
        user=user_with_profile,
        uid='test_uid_1',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 2}],
        shipping={'name': 'テスト ユーザー', 'zipcode': '1000001'}
    )

    # 別のユーザーの注文を作成
    from django.contrib.auth import get_user_model
    User = get_user_model()
    other_user = User.objects.create_user(
        email='other@example.com',
        password='testpass123',
        username='otheruser'
    )
    order2 = Order.objects.create(
        user=other_user,
        uid='test_uid_2',
        amount=500,
        tax_included=550,
        items=[{'pk': published_card.pk, 'quantity': 1}],
        shipping={'name': '他のユーザー', 'zipcode': '2000001'}
    )

    response = authenticated_client.get('/orders/')
    assert response.status_code == 200

    # 自分の注文のみが表示されることを確認
    orders = list(response.context['object_list'])
    assert len(orders) == 1
    assert orders[0].id == order1.id
    assert order2.id not in [o.id for o in orders]


@pytest.mark.django_db
def test_order_index_view_ordered_by_created_at(authenticated_client, user_with_profile, published_card):
    """注文が作成日時の降順で表示されることを確認"""
    # 古い注文
    order1 = Order.objects.create(
        user=user_with_profile,
        uid='test_uid_1',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 2}],
        shipping={'name': 'テスト ユーザー'}
    )
    order1.created_at = timezone.now() - timezone.timedelta(days=2)
    order1.save()

    # 新しい注文
    order2 = Order.objects.create(
        user=user_with_profile,
        uid='test_uid_2',
        amount=500,
        tax_included=550,
        items=[{'pk': published_card.pk, 'quantity': 1}],
        shipping={'name': 'テスト ユーザー'}
    )
    order2.created_at = timezone.now() - timezone.timedelta(days=1)
    order2.save()

    response = authenticated_client.get('/orders/')
    assert response.status_code == 200

    orders = list(response.context['object_list'])
    assert len(orders) == 2
    # 新しい注文が先に表示される
    assert orders[0].id == order2.id
    assert orders[1].id == order1.id


@pytest.mark.django_db
def test_order_detail_view_requires_login(client, user_with_profile, published_card):
    """注文詳細ページはログインが必要"""
    order = Order.objects.create(
        user=user_with_profile,
        uid='test_uid',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 2}],
        shipping={'name': 'テスト ユーザー'}
    )

    response = client.get(f'/orders/{order.id}/')
    assert response.status_code == 302  # ログインページにリダイレクト


@pytest.mark.django_db
def test_order_detail_view_shows_order(authenticated_client, user_with_profile, published_card):
    """注文詳細が正しく表示されることを確認"""
    order = Order.objects.create(
        user=user_with_profile,
        uid='test_uid',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 2,
                'name': published_card.name}],
        shipping={'name': 'テスト ユーザー', 'zipcode': '1000001'}
    )

    response = authenticated_client.get(f'/orders/{order.id}/')
    assert response.status_code == 200
    assert response.context['object'].id == order.id

    # コンテキストに items と shipping が含まれていることを確認
    assert 'items' in response.context
    assert 'shipping' in response.context
    assert response.context['shipping']['name'] == 'テスト ユーザー'


@pytest.mark.django_db
def test_order_detail_view_prevents_access_to_other_user_order(authenticated_client, user_with_profile, published_card):
    """他のユーザーの注文にアクセスできないことを確認"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    other_user = User.objects.create_user(
        email='other@example.com',
        password='testpass123',
        username='otheruser'
    )

    order = Order.objects.create(
        user=other_user,
        uid='test_uid',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 2}],
        shipping={'name': '他のユーザー'}
    )

    response = authenticated_client.get(f'/orders/{order.id}/')
    assert response.status_code == 404  # アクセスできない
