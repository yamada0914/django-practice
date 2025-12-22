"""
アカウント関連のビューのテスト
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from base.models import Profile

User = get_user_model()


@pytest.mark.django_db
def test_login_view_get(client):
    """ログインページが表示されることを確認"""
    response = client.get('/account/login/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_success(client, user):
    """正しい認証情報でログインできることを確認"""
    response = client.post('/account/login/', {
        'username': user.email,
        'password': 'testpass123'
    })
    assert response.status_code == 302  # リダイレクト


@pytest.mark.django_db
def test_login_failure(client, user):
    """間違った認証情報でログインできないことを確認"""
    response = client.post('/account/login/', {
        'username': user.email,
        'password': 'wrongpassword'
    })
    assert response.status_code == 200  # エラーメッセージが表示される


@pytest.mark.django_db
def test_signup_view_get(client):
    """サインアップページが表示されることを確認"""
    response = client.get('/account/signup/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_signup_success(client):
    """新規ユーザー登録が成功することを確認"""
    response = client.post('/account/signup/', {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpass123',
        'last_name': '山田',
        'first_name': '太郎',
        'last_name_kana': 'ヤマダ',
        'first_name_kana': 'タロウ',
        'company': 'テスト会社',
        'tel': '09012345678'
    })
    assert response.status_code == 302  # リダイレクト
    assert response.url == '/'

    # ユーザーが作成されたことを確認
    user = User.objects.get(email='newuser@example.com')
    assert user is not None
    assert user.username == 'newuser'

    # プロフィールが作成されたことを確認
    profile = user.profile
    assert profile is not None
    assert profile.name == '山田 太郎'
    assert profile.last_name == '山田'
    assert profile.first_name == '太郎'


@pytest.mark.django_db
def test_account_update_view_requires_login(client):
    """アカウント更新ページはログインが必要"""
    response = client.get('/account/')
    assert response.status_code == 302  # ログインページにリダイレクト


@pytest.mark.django_db
def test_account_update_view_get(authenticated_client):
    """アカウント更新ページが表示されることを確認"""
    response = authenticated_client.get('/account/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_account_update_success(authenticated_client, user_with_profile):
    """アカウント情報の更新が成功することを確認"""
    response = authenticated_client.post('/account/', {
        'username': 'updateduser',
        'email': 'updated@example.com',
        'name': '更新 ユーザー',
        'zipcode': '1000002',
        'prefecture': '東京都',
        'city': '中央区',
        'address1': '中央1-1-1',
        'address2': '',
        'tel': '09087654321'
    })
    assert response.status_code == 302  # リダイレクト

    # ユーザー情報が更新されたことを確認
    user_with_profile.refresh_from_db()
    assert user_with_profile.username == 'updateduser'
    assert user_with_profile.email == 'updated@example.com'

    # プロフィール情報が更新されたことを確認
    profile = user_with_profile.profile
    profile.refresh_from_db()
    assert profile.name == '更新 ユーザー'
    assert profile.zipcode == '1000002'


@pytest.mark.django_db
def test_profile_update_view_requires_login(client):
    """プロフィール更新ページはログインが必要"""
    response = client.get('/profile/')
    assert response.status_code == 302  # ログインページにリダイレクト


@pytest.mark.django_db
def test_profile_update_view_get(authenticated_client):
    """プロフィール更新ページが表示されることを確認"""
    response = authenticated_client.get('/profile/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_profile_update_success(authenticated_client, user_with_profile):
    """プロフィール情報の更新が成功することを確認"""
    response = authenticated_client.post('/profile/', {
        'last_name': '更新',
        'first_name': '太郎',
        'last_name_kana': 'コウシン',
        'first_name_kana': 'タロウ',
        'company': '更新会社',
        'name': '更新 太郎',
        'zipcode': '1000003',
        'prefecture': '大阪府',
        'city': '大阪市',
        'address1': '大阪1-1-1',
        'address2': 'ビル101',
        'tel': '09011111111'
    })
    assert response.status_code == 302  # リダイレクト

    # プロフィール情報が更新されたことを確認
    profile = user_with_profile.profile
    profile.refresh_from_db()
    assert profile.last_name == '更新'
    assert profile.first_name == '太郎'
    assert profile.name == '更新 太郎'
    assert profile.zipcode == '1000003'
    assert profile.prefecture == '大阪府'
