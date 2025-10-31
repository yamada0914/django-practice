"""
カード関連のビュークラス
"""
from django.views.generic import ListView, DetailView, TemplateView
from django.core.exceptions import ObjectDoesNotExist
from base.models import Card, Category, Tag
from base.utils import load_banners_from_csv, get_popular_cards, prepare_slider_data
from base.constants import FOUR_BANNERS_CONFIG
from .base_views import BaseCardView


class IndexListView(BaseCardView, ListView):
    """インデックスページのビュー"""

    model = Card
    template_name = 'pages/index.html'
    queryset = Card.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())

        # パンくずリストのデータを準備（ホームページ用）
        breadcrumb_items = self._prepare_breadcrumb_items()
        context['index_breadcrumb_items'] = breadcrumb_items

        # バナーデータを追加
        context.update({
            'BANNERS': load_banners_from_csv(),
            'FOUR_BANNERS': FOUR_BANNERS_CONFIG,
        })

        # 人気カードのスライダーデータを準備
        popular_cards = get_popular_cards()
        context['POPULAR_SLIDER_DATA'] = prepare_slider_data(popular_cards)

        return context


class CardDetailView(BaseCardView, DetailView):
    """カード詳細ページのビュー"""

    model = Card
    template_name = 'pages/card.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self._update_recent_cards_session(request, self.object)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())
        context.update(self._prepare_slider_context())

        # パンくずリストのデータを準備
        breadcrumb_items = self._prepare_breadcrumb_items(
            pack=self.object.pack if self.object else None,
            card=self.object
        )

        # ログイン状態と最近チェックした商品を追加
        context.update({
            'is_authenticated': self.request.user.is_authenticated,
            'RECENT_CARDS': self._get_recent_cards(self.request),
            'card_breadcrumb_items': breadcrumb_items,
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
            return Card.objects.none()

    def get_context_data(self, **kwargs):
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
            return Card.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())
        tag_name = getattr(self, 'tag', None)
        context["title"] = f"Tag #{tag_name.name if tag_name else 'Unknown'}"
        return context


class HelpView(TemplateView):
    """ヘルプページのビュー"""

    template_name = 'pages/help.html'
