"""
ベースビュークラスと共通機能
"""
from typing import List, Dict
from django.views.generic import ListView, DetailView, TemplateView
from django.core.exceptions import ObjectDoesNotExist
from base.models import Card, Category, Pack
from base.utils import (
    prepare_slider_data, get_popular_cards
)
from base.constants import (
    MAX_RECENT_CARDS, RECENT_CARDS_SESSION_KEY
)


class BaseCardView:
    """カード関連ビューの基底クラス"""

    def get_categories_context(self):
        """カテゴリーデータをコンテキストに追加"""
        categories = Category.objects.prefetch_related('packs').all()
        return {'CATEGORIES': categories}

    def _prepare_slider_context(self):
        """スライダー関連のコンテキストを準備"""
        popular_cards = get_popular_cards()
        slider_data = prepare_slider_data(popular_cards)

        return {
            'RECOMMEND_SLIDER_DATA': slider_data,
            'POPULAR_SLIDER_DATA': slider_data,
        }

    def _prepare_breadcrumb_items(self, pack=None, category=None, card=None, url_parameter=None) -> List[Dict]:
        """パンくずリストのデータを準備する共通メソッド"""
        breadcrumb_items = []

        # 'all' の場合は特別な処理
        if url_parameter == 'all':
            breadcrumb_items.append({
                'name': 'all',
                'url': '/collections/all/',
                'is_active': False
            })
            return breadcrumb_items

        if pack and pack.category:
            # カテゴリー
            breadcrumb_items.append({
                'name': pack.category.name,
                'url': f'/collections/{pack.category.series_code}/',
                'is_active': False
            })
            # パック（常にリンク）
            breadcrumb_items.append({
                'name': pack.name,
                'url': f'/collections/{pack.series_code}/',
                'is_active': False
            })
        elif category:
            # 現在のカテゴリー
            breadcrumb_items.append({
                'name': category.name,
                'url': f'/collections/{category.series_code}/',
                'is_active': False
            })

        # カード詳細の場合のみカード名を追加
        if card:
            breadcrumb_items.append({
                'name': card.display_name,
                'url': None,
                'is_active': True
            })

        return breadcrumb_items

    def _update_recent_cards_session(self, request, card) -> None:
        """セッションの最近チェックした商品を更新"""
        recent_card_ids = request.session.get(RECENT_CARDS_SESSION_KEY, [])
        current_card_id = str(card.pk)

        if current_card_id in recent_card_ids:
            recent_card_ids.remove(current_card_id)
        recent_card_ids.insert(0, current_card_id)

        # 最大件数まで保持
        recent_card_ids = recent_card_ids[:MAX_RECENT_CARDS]
        request.session[RECENT_CARDS_SESSION_KEY] = recent_card_ids

    def _get_recent_cards(self, request) -> List[Card]:
        """最近チェックした商品を取得"""
        recent_card_ids = request.session.get(RECENT_CARDS_SESSION_KEY, [])
        recent_cards: List[Card] = []

        for card_id in recent_card_ids:
            try:
                card = Card.objects.get(pk=card_id, is_published=True)
                recent_cards.append(card)
            except ObjectDoesNotExist:
                continue

        return recent_cards
