"""
ユーティリティ関数のテスト
"""
import pytest
import json
from unittest.mock import patch, mock_open
from base.utils import prepare_slider_data, get_popular_cards, clear_cart, load_banners_from_csv
from base.models import Card
from base.constants import SLIDER_ITEMS_PER_GROUP, MAX_POPULAR_CARDS


@pytest.mark.django_db
def test_prepare_slider_data(published_card):
    """prepare_slider_data が正しく動作することを確認"""
    cards = [published_card]
    result = prepare_slider_data(cards)

    assert result != '[]'
    data = json.loads(result)
    assert len(data) == 1
    assert len(data[0]) == 1
    assert data[0][0]['pk'] == published_card.pk
    assert data[0][0]['name'] == published_card.display_name


@pytest.mark.django_db
def test_prepare_slider_data_empty_list():
    """prepare_slider_data が空のリストで正しく動作することを確認"""
    result = prepare_slider_data([])
    assert result == '[]'


@pytest.mark.django_db
def test_prepare_slider_data_multiple_groups(published_card, unpublished_card):
    """prepare_slider_data が複数グループを作成することを確認"""
    unpublished_card.is_published = True
    unpublished_card.save()

    cards = [published_card, unpublished_card]
    # SLIDER_ITEMS_PER_GROUP が 1 の場合、2つのグループが作成される
    result = prepare_slider_data(cards, n=1)

    data = json.loads(result)
    assert len(data) == 2
    assert len(data[0]) == 1
    assert len(data[1]) == 1


@pytest.mark.django_db
def test_get_popular_cards(published_card, unpublished_card):
    """get_popular_cards が人気カードを正しく取得することを確認"""
    # 販売数を設定
    published_card.sold_count = 10
    published_card.save()

    unpublished_card.is_published = True
    unpublished_card.sold_count = 5
    unpublished_card.save()

    popular_cards = get_popular_cards()

    # 公開済みのカードのみが含まれることを確認
    assert published_card in popular_cards
    assert unpublished_card in popular_cards

    # 販売数の降順でソートされていることを確認
    sold_counts = [card.sold_count for card in popular_cards]
    assert sold_counts == sorted(sold_counts, reverse=True)

    # 未公開のカードは含まれないことを確認
    unpublished_card.is_published = False
    unpublished_card.sold_count = 20  # より多く売れているが未公開
    unpublished_card.save()

    popular_cards = get_popular_cards()
    assert published_card in popular_cards
    assert unpublished_card not in popular_cards


@pytest.mark.django_db
def test_get_popular_cards_limit(published_card):
    """get_popular_cards が MAX_POPULAR_CARDS を超えないことを確認"""
    # 複数のカードを作成
    cards = []
    for i in range(MAX_POPULAR_CARDS + 5):
        card = Card.objects.create(
            name=f'カード{i}',
            price=100,
            stock=10,
            is_published=True,
            sold_count=i,
            pack=published_card.pack
        )
        cards.append(card)

    popular_cards = get_popular_cards()

    assert len(popular_cards) <= MAX_POPULAR_CARDS


@pytest.mark.django_db
def test_clear_cart(client, published_card):
    """clear_cart がカートをクリアすることを確認"""
    from django.test import RequestFactory
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.auth import get_user_model

    # リクエストオブジェクトを作成
    factory = RequestFactory()
    request = factory.get('/')

    # セッションミドルウェアを適用
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()

    # カートに商品を追加
    request.session['cart'] = {
        'items': {published_card.pk: 2},
        'total': published_card.price * 2
    }
    request.session.save()

    # カートが存在することを確認
    assert 'cart' in request.session
    assert request.session['cart']['items']

    # カートをクリア
    clear_cart(request)

    # カートが削除されていることを確認
    assert 'cart' not in request.session


@patch('base.utils.settings')
@patch('builtins.open', new_callable=mock_open, read_data="name,url,image\nバナー1,https://example.com/banner1,image1.jpg\nバナー2,https://example.com/banner2,image2.jpg")
def test_load_banners_from_csv_success(mock_file, mock_settings):
    """load_banners_from_csv が CSV ファイルを正しく読み込むことを確認"""
    from django.conf import settings
    mock_settings.BASE_DIR = '/test/path'

    banners = load_banners_from_csv()

    assert len(banners) == 2
    assert banners[0]['name'] == 'バナー1'
    assert banners[0]['url'] == 'https://example.com/banner1'
    assert banners[1]['name'] == 'バナー2'
    assert banners[1]['url'] == 'https://example.com/banner2'


@patch('base.utils.settings')
@patch('builtins.open', side_effect=FileNotFoundError)
def test_load_banners_from_csv_file_not_found(mock_file, mock_settings):
    """load_banners_from_csv がファイルが見つからない場合に空のリストを返すことを確認"""
    from django.conf import settings
    mock_settings.BASE_DIR = '/test/path'

    banners = load_banners_from_csv()
    assert banners == []


@patch('base.utils.settings')
@patch('builtins.open', side_effect=Exception("読み込みエラー"))
def test_load_banners_from_csv_error(mock_file, mock_settings):
    """load_banners_from_csv がエラー発生時に空のリストを返すことを確認"""
    from django.conf import settings
    mock_settings.BASE_DIR = '/test/path'

    banners = load_banners_from_csv()
    assert banners == []
