"""共通の pytest fixture を定義"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from base.models import Card, Category, Pack, Tag

User = get_user_model()


@pytest.fixture
def image_file():
    """簡易的なダミー画像を生成する。"""

    def _create(filename="card.jpg"):
        return SimpleUploadedFile(filename, b"fake image bytes", content_type="image/jpeg")

    return _create


@pytest.fixture
def category(db):
    return Category.objects.create(series_code="SV1", name="Scarlet & Violet")


@pytest.fixture
def pack(category):
    return Pack.objects.create(
        name="Starter Pack",
        slug="starter-pack",
        category=category,
        series_code="sv1-starter"
    )


@pytest.fixture
def tag(db):
    return Tag.objects.create(slug="fire", name="Fire")


@pytest.fixture
def published_card(pack, tag, image_file):
    card = Card.objects.create(
        pokemon_id="025",
        name="ピカチュウ",
        pokemon_name="ピカチュウ",
        english_name="Pikachu",
        price=500,
        stock=5,
        is_published=True,
        pack=pack,
        image=image_file("pikachu.jpg"),
    )
    card.tags.add(tag)
    return card


@pytest.fixture
def unpublished_card(pack, image_file):
    return Card.objects.create(
        pokemon_id="026",
        name="ライチュウ",
        pokemon_name="ライチュウ",
        english_name="Raichu",
        price=400,
        stock=2,
        is_published=False,
        pack=pack,
        image=image_file("raichu.jpg"),
    )


@pytest.fixture
def user(db):
    """テスト用のユーザーを作成"""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        username='testuser'
    )


@pytest.fixture
def user_with_profile(user):
    """プロフィール情報が入力済みのユーザーを作成"""
    profile = user.profile
    profile.name = 'テスト ユーザー'
    profile.zipcode = '1000001'
    profile.prefecture = '東京都'
    profile.city = '千代田区'
    profile.address1 = '千代田1-1-1'
    profile.address2 = ''
    profile.tel = '09012345678'
    profile.save()
    return user


@pytest.fixture
def authenticated_client(client, user_with_profile):
    """認証済みのクライアントを作成"""
    client.force_login(user_with_profile)
    return client
