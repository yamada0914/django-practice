"""
モデルのテスト
"""
import pytest
from django.contrib.auth import get_user_model
from base.models import Order, Card, Profile, User
from django.utils import timezone

UserModel = get_user_model()


@pytest.mark.django_db
def test_order_confirm_success(user_with_profile, published_card):
    """注文の確定が成功することを確認"""
    order = Order.objects.create(
        user=user_with_profile,
        uid='test_uid',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 1}],
        shipping={'name': 'テスト ユーザー'}
    )

    assert order.is_confirmed is False
    result = order.confirm()
    assert result is True

    order.refresh_from_db()
    assert order.is_confirmed is True


@pytest.mark.django_db
def test_order_confirm_already_confirmed(user_with_profile, published_card):
    """既に確定済みの注文は再度確定できないことを確認"""
    order = Order.objects.create(
        user=user_with_profile,
        uid='test_uid',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 1}],
        shipping={'name': 'テスト ユーザー'},
        is_confirmed=True
    )

    result = order.confirm()
    assert result is False

    order.refresh_from_db()
    assert order.is_confirmed is True


@pytest.mark.django_db
def test_card_display_name_with_all_fields(pack, tag):
    """Card の display_name がすべてのフィールドを含むことを確認"""
    card = Card.objects.create(
        name='ピカチュウ',
        rarity='R',
        type='雷',
        number='001/100',
        series_code='SV1',
        pack=pack
    )
    card.tags.add(tag)

    expected = 'ピカチュウ(R){雷}〈001/100〉[SV1]'
    assert card.display_name == expected


@pytest.mark.django_db
def test_card_display_name_minimal(pack):
    """Card の display_name が最小限のフィールドでも動作することを確認"""
    card = Card.objects.create(
        name='ピカチュウ',
        pack=pack
    )

    assert card.display_name == 'ピカチュウ'


@pytest.mark.django_db
def test_card_display_name_partial_fields(pack):
    """Card の display_name が一部のフィールドでも動作することを確認"""
    card = Card.objects.create(
        name='ピカチュウ',
        rarity='R',
        series_code='SV1',
        pack=pack
    )

    assert card.display_name == 'ピカチュウ(R)[SV1]'


@pytest.mark.django_db
def test_user_creates_profile_automatically():
    """ユーザー作成時にプロフィールが自動生成されることを確認"""
    user = User.objects.create_user(
        email='newuser@example.com',
        password='testpass123',
        username='newuser'
    )

    # プロフィールが自動生成されていることを確認
    assert hasattr(user, 'profile')
    assert isinstance(user.profile, Profile)


@pytest.mark.django_db
def test_order_str_returns_id(user_with_profile, published_card):
    """Order の __str__ が id を返すことを確認"""
    order = Order.objects.create(
        user=user_with_profile,
        uid='test_uid',
        amount=1000,
        tax_included=1100,
        items=[{'pk': published_card.pk, 'quantity': 1}],
        shipping={'name': 'テスト ユーザー'}
    )

    assert str(order) == order.id


@pytest.mark.django_db
def test_card_str_returns_name(pack):
    """Card の __str__ が name を返すことを確認"""
    card = Card.objects.create(
        name='ピカチュウ',
        pack=pack
    )

    assert str(card) == 'ピカチュウ'
