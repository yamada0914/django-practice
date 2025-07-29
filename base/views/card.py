from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from base.models import Card, Category, Tag
from typing import List, Dict, Union, Optional
import csv
import os
import json
import logging

logger = logging.getLogger(__name__)

# 定数定義
SLIDER_ITEMS_PER_GROUP = 3
MAX_POPULAR_CARDS = 12
MAX_RECENT_CARDS = 12
RECENT_CARDS_SESSION_KEY = 'recent_cards'

# バナー設定
BANNER_CSV_PATH = os.path.join('data', 'csv', 'banners.csv')
FOUR_BANNERS_CONFIG = [
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2supB.webp",
        "url": "#"
    },
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2211_hare2oripa.webp",
        "url": "#"
    },
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2deckB.webp",
        "url": "#"
    },
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2tumeB.webp",
        "url": "#"
    },
]

# 型定義
SliderItem = Dict[str, Union[str, int]]
SliderGroup = List[SliderItem]
SliderData = List[SliderGroup]
BannerData = Dict[str, str]
ContextData = Dict[str, Union[str, int, bool, QuerySet,
                              List[Card], SliderData, List[BannerData]]]


def batch(lst: List[Card], n: int) -> List[List[Card]]:
    """リストを指定した数ずつグループ化する関数

    Args:
        lst: グループ化するリスト
        n: 各グループの要素数

    Returns:
        グループ化されたリストのリスト
    """
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def card_to_slider_item(card: Card) -> SliderItem:
    """カードオブジェクトをスライダーアイテムに変換する関数

    Args:
        card: 変換するカードオブジェクト

    Returns:
        スライダーアイテムの辞書
    """
    return {
        'name': card.display_name or '',
        'pk': card.pk,
        'image': card.image.url if card.image else '',
        'price': card.price or 0,
        'stock': card.stock or 0
    }


def prepare_slider_data(groups: List[List[Card]]) -> str:
    """スライダー用の JSON データを準備する関数

    Args:
        groups: カードのグループ化されたリスト

    Returns:
        スライダー用の JSON 文字列
    """
    if not groups:
        return '[]'

    try:
        slider_data: SliderData = []
        for group in groups:
            if not group:
                continue
            group_data = [card_to_slider_item(card) for card in group if card]
            if group_data:
                slider_data.append(group_data)

        return json.dumps(slider_data) if slider_data else '[]'
    except Exception as e:
        logger.error(f"スライダーデータの準備中にエラーが発生: {e}")
        return '[]'


def get_popular_cards() -> List[Card]:
    """人気カードを取得する共通関数

    Returns:
        売上順でソートされた人気カードのリスト
    """
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


def get_four_banners() -> List[BannerData]:
    """4 カラムバナーデータを取得する関数

    Returns:
        4 カラムバナーのリスト
    """
    return FOUR_BANNERS_CONFIG.copy()


class BaseCardView:
    """カード関連ビューの基底クラス"""

    def get_categories_context(self) -> ContextData:
        """カテゴリーデータをコンテキストに追加"""
        return {'CATEGORIES': Category.objects.all()}


class IndexListView(BaseCardView, ListView):
    """インデックスページのビュー"""

    model = Card
    template_name = 'pages/index.html'
    queryset = Card.objects.filter(is_published=True)

    def get_context_data(self, **kwargs) -> ContextData:
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())

        # バナーデータを追加
        context.update({
            'BANNERS': load_banners_from_csv(),
            'FOUR_BANNERS': get_four_banners(),
        })

        # 人気カードのスライダーデータを準備
        popular_cards = get_popular_cards()
        popular_groups = batch(popular_cards, SLIDER_ITEMS_PER_GROUP)
        context['POPULAR_SLIDER_DATA'] = prepare_slider_data(popular_groups)

        return context


class CardDetailView(BaseCardView, DetailView):
    """カード詳細ページのビュー"""

    model = Card
    template_name = 'pages/item.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._update_recent_cards_session(request)
        return super().get(request, *args, **kwargs)

    def _update_recent_cards_session(self, request) -> None:
        """セッションの最近チェックした商品を更新"""
        recent_card_ids = request.session.get(RECENT_CARDS_SESSION_KEY, [])
        current_card_id = str(self.object.pk)

        if current_card_id in recent_card_ids:
            recent_card_ids.remove(current_card_id)
        recent_card_ids.insert(0, current_card_id)

        # 最大件数まで保持
        recent_card_ids = recent_card_ids[:MAX_RECENT_CARDS]
        request.session[RECENT_CARDS_SESSION_KEY] = recent_card_ids

    def _get_recent_cards(self) -> List[Card]:
        """最近チェックした商品を取得"""
        recent_card_ids = self.request.session.get(
            RECENT_CARDS_SESSION_KEY, [])
        recent_cards: List[Card] = []

        for card_id in recent_card_ids:
            try:
                card = Card.objects.get(pk=card_id, is_published=True)
                recent_cards.append(card)
            except ObjectDoesNotExist:
                continue

        return recent_cards

    def _prepare_slider_context(self) -> ContextData:
        """スライダー関連のコンテキストを準備"""
        popular_cards = get_popular_cards()
        groups = batch(popular_cards, SLIDER_ITEMS_PER_GROUP)

        return {
            'RECOMMEND_SLIDER_DATA': prepare_slider_data(groups),
            'POPULAR_SLIDER_DATA': prepare_slider_data(groups),
        }

    def get_context_data(self, **kwargs) -> ContextData:
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())
        context.update(self._prepare_slider_context())

        # ログイン状態と最近チェックした商品を追加
        context.update({
            'is_authenticated': self.request.user.is_authenticated,
            'RECENT_CARDS': self._get_recent_cards(),
        })

        return context


class CategoryListView(BaseCardView, ListView):
    """カテゴリーページのビュー"""

    model = Card
    template_name = 'pages/list.html'
    paginate_by = 2

    def get_queryset(self):
        try:
            self.category = Category.objects.get(slug=self.kwargs['pk'])
            return Card.objects.filter(
                is_published=True,
                pack__category=self.category
            )
        except ObjectDoesNotExist:
            logger.error(f"カテゴリが見つかりません: {self.kwargs['pk']}")
            return Card.objects.none()

    def get_context_data(self, **kwargs) -> ContextData:
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())
        category_name = getattr(self, "category", None)
        context['title'] = f'Category #{category_name.name if category_name else "Unknown"}'
        return context


class TagListView(BaseCardView, ListView):
    """タグページのビュー"""

    model = Card
    template_name = 'pages/list.html'
    paginate_by = 2

    def get_queryset(self):
        try:
            self.tag = Tag.objects.get(slug=self.kwargs['pk'])
            return Card.objects.filter(is_published=True, tags=self.tag)
        except ObjectDoesNotExist:
            logger.error(f"タグが見つかりません: {self.kwargs['pk']}")
            return Card.objects.none()

    def get_context_data(self, **kwargs) -> ContextData:
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())
        tag_name = getattr(self, 'tag', None)
        context["title"] = f"Tag #{tag_name.name if tag_name else 'Unknown'}"
        return context


class HelpView(TemplateView):
    """ヘルプページのビュー"""

    template_name = 'pages/help.html'
