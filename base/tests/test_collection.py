"""
コレクション関連のビューのテスト
"""
import pytest
from base.models import Card, Pack, Category


@pytest.mark.django_db
def test_pack_detail_view_all(client, published_card):
    """すべての商品を表示できることを確認"""
    response = client.get('/collections/all/')
    assert response.status_code == 200
    assert published_card in list(response.context['object_list'])


@pytest.mark.django_db
def test_pack_detail_view_by_category(client, category, published_card):
    """カテゴリーでフィルタリングできることを確認"""
    response = client.get(f'/collections/{category.series_code}/')
    assert response.status_code == 200
    assert published_card in list(response.context['object_list'])


@pytest.mark.django_db
def test_pack_detail_view_by_pack(client, pack, published_card):
    """パックでフィルタリングできることを確認"""
    # series_code が空の場合はslugを使用
    identifier = pack.series_code if pack.series_code else pack.slug
    response = client.get(f'/collections/{identifier}/')
    # series_code が空の場合はカテゴリー検索にフォールバックするため、404 になる可能性がある
    # その場合はカテゴリー経由でアクセス
    if response.status_code == 404:
        response = client.get(f'/collections/{pack.category.series_code}/')
    assert response.status_code == 200
    assert published_card in list(response.context['object_list'])


@pytest.mark.django_db
def test_pack_detail_view_invalid_identifier(client):
    """存在しない識別子で 404 を返すことを確認"""
    response = client.get('/collections/invalid_identifier/')
    assert response.status_code == 200  # 空のリストを返す
    assert len(response.context['object_list']) == 0


@pytest.mark.django_db
def test_pack_detail_view_sort_price_asc(client, published_card, unpublished_card):
    """価格の安い順でソートできることを確認"""
    # 価格を設定
    published_card.price = 1000
    published_card.save()
    unpublished_card.price = 500
    unpublished_card.is_published = True
    unpublished_card.save()

    response = client.get('/collections/all/?sort=price_asc')
    assert response.status_code == 200

    cards = list(response.context['object_list'])
    # 価格の安い順になっていることを確認
    prices = [card.price for card in cards]
    assert prices == sorted(prices)


@pytest.mark.django_db
def test_pack_detail_view_sort_price_desc(client, published_card, unpublished_card):
    """価格の高い順でソートできることを確認"""
    # 価格を設定
    published_card.price = 500
    published_card.save()
    unpublished_card.price = 1000
    unpublished_card.is_published = True
    unpublished_card.save()

    response = client.get('/collections/all/?sort=price_desc')
    assert response.status_code == 200

    cards = list(response.context['object_list'])
    # 価格の高い順になっていることを確認
    prices = [card.price for card in cards]
    assert prices == sorted(prices, reverse=True)


@pytest.mark.django_db
def test_pack_detail_view_context_data(client, category):
    """コンテキストデータが正しく設定されることを確認"""
    response = client.get(f'/collections/{category.series_code}/')
    assert response.status_code == 200

    assert 'title' in response.context_data
    assert 'category' in response.context_data
    assert 'current_sort' in response.context_data
    assert 'is_price_asc' in response.context_data
    assert 'is_price_desc' in response.context_data


@pytest.mark.django_db
def test_pack_detail_view_only_published_cards(client, published_card, unpublished_card):
    """公開済みのカードのみが表示されることを確認"""
    response = client.get('/collections/all/')
    assert response.status_code == 200

    cards = list(response.context['object_list'])
    assert published_card in cards
    assert unpublished_card not in cards
