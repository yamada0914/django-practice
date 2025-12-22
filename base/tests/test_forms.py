"""
フォームのテスト
"""
import pytest
from django.contrib.auth import get_user_model
from base.forms import UserCreationForm, ProfileForm, AccountUpdateForm
from base.models import Profile

User = get_user_model()


@pytest.mark.django_db
def test_user_creation_form_valid():
    """UserCreationForm が有効なデータで動作することを確認"""
    form = UserCreationForm({
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    assert form.is_valid()

    user = form.save()
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.check_password('testpass123')


@pytest.mark.django_db
def test_user_creation_form_invalid_email():
    """UserCreationForm が無効なメールアドレスを拒否することを確認"""
    form = UserCreationForm({
        'username': 'testuser',
        'email': 'invalid-email',
        'password': 'testpass123'
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_user_creation_form_duplicate_email():
    """UserCreationForm が重複したメールアドレスを拒否することを確認"""
    User.objects.create_user(
        email='existing@example.com',
        password='testpass123',
        username='existinguser'
    )

    form = UserCreationForm({
        'username': 'newuser',
        'email': 'existing@example.com',
        'password': 'testpass123'
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_profile_form_valid(user):
    """ProfileForm が有効なデータで動作することを確認"""
    form = ProfileForm({
        'last_name': '山田',
        'first_name': '太郎',
        'last_name_kana': 'ヤマダ',
        'first_name_kana': 'タロウ',
        'company': 'テスト会社',
        'name': '山田 太郎',
        'zipcode': '1000001',
        'prefecture': '東京都',
        'city': '千代田区',
        'address1': '千代田1-1-1',
        'address2': '',
        'tel': '09012345678'
    }, instance=user.profile)
    assert form.is_valid()

    profile = form.save()
    assert profile.last_name == '山田'
    assert profile.first_name == '太郎'
    assert profile.name == '山田 太郎'


@pytest.mark.django_db
def test_profile_form_saves_name_from_last_and_first(user):
    """ProfileForm が姓と名から name を自動生成することを確認"""
    form = ProfileForm({
        'last_name': '佐藤',
        'first_name': '花子',
        'last_name_kana': '',
        'first_name_kana': '',
        'company': '',
        'name': '',
        'zipcode': '',
        'prefecture': '',
        'city': '',
        'address1': '',
        'address2': '',
        'tel': ''
    }, instance=user.profile)
    assert form.is_valid()

    profile = form.save()
    assert profile.name == '佐藤 花子'


@pytest.mark.django_db
def test_account_update_form_valid(user):
    """AccountUpdateForm が有効なデータで動作することを確認"""
    form = AccountUpdateForm({
        'username': 'updateduser',
        'email': 'updated@example.com'
    }, instance=user)
    assert form.is_valid()

    updated_user = form.save()
    assert updated_user.username == 'updateduser'
    assert updated_user.email == 'updated@example.com'


@pytest.mark.django_db
def test_account_update_form_invalid_email(user):
    """AccountUpdateForm が無効なメールアドレスを拒否することを確認"""
    form = AccountUpdateForm({
        'username': 'testuser',
        'email': 'invalid-email'
    }, instance=user)
    assert not form.is_valid()
