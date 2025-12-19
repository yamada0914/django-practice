"""
ビューで使用されるユーティリティ関数
"""
from __future__ import annotations

import csv
import json
import logging
import os
import datetime
from typing import List, Dict, Union
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from base.constants import (
    ID_LENGTH, SLIDER_ITEMS_PER_GROUP, MAX_POPULAR_CARDS,
    RECENT_CARDS_SESSION_KEY, BANNER_CSV_PATH, FOUR_BANNERS_CONFIG
)

logger = logging.getLogger(__name__)


def create_id() -> str:
    """ランダムなIDを生成"""
    return get_random_string(ID_LENGTH)


def custom_timestamp_id() -> str:
    """タイムスタンプベースの ID を生成"""
    dt = datetime.datetime.now()
    return dt.strftime('%Y%m%d%H%M%S%f')


# 型定義
SliderItem = Dict[str, Union[str, int]]
SliderGroup = List[SliderItem]
SliderData = List[SliderGroup]
BannerData = Dict[str, str]


def batch(lst: List[Card], n: int) -> List[List[Card]]:
    """リストを指定した数ずつグループ化する関数

    Args:
        lst: グループ化するリスト
        n: 各グループの要素数

    Returns:
        グループ化されたリストのリスト
    """
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def prepare_slider_data(cards: list[Card], n: int = SLIDER_ITEMS_PER_GROUP) -> str:
    """カード一覧を n 件ずつグループ化しスライダー用の JSON 文字列に変換"""
    groups = [cards[i:i + n] for i in range(0, len(cards), n)]
    slider_data = []
    for group in groups:
        group_data = [{
            'name': card.display_name or '',
            'pk': card.pk,
            'image': card.image.url if card.image else '',
            'price': card.price or 0,
            'stock': card.stock or 0
        } for card in group if card]
        if group_data:
            slider_data.append(group_data)
    try:
        return json.dumps(slider_data) if slider_data else '[]'
    except Exception as e:
        logger.error(f"スライダーデータの準備中にエラーが発生: {e}")
        return '[]'


def get_popular_cards() -> List[Card]:
    """人気カードを取得する共通関数

    Returns:
        売上順でソートされた人気カードのリスト
    """
    from base.models import Card
    return list(Card.objects.filter(
        is_published=True
    ).order_by('-sold_count')[:MAX_POPULAR_CARDS])


def load_banners_from_csv() -> List[BannerData]:
    """バナー CSV ファイルを読み込む関数

    Returns:
        バナーデータのリスト
    """
    csv_path = os.path.join(settings.BASE_DIR, BANNER_CSV_PATH)

    try:
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        logger.warning(f"バナー CSV ファイルが見つかりません: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"バナー CSV ファイルの読み込み中にエラーが発生: {e}")
        return []


def clear_cart(request):
    """カート情報をセッションから削除"""
    if 'cart' in request.session:
        del request.session['cart']
