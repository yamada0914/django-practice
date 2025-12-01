import pytest
from django.contrib.auth import get_user_model


def test_base_app_registered(settings):
    assert "base" in settings.INSTALLED_APPS


@pytest.mark.django_db
def test_database_available():
    # シンプルに User モデルへクエリを投げて DB が使えることを確認
    assert get_user_model().objects.count() >= 0
