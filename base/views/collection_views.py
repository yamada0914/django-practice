"""
コレクション関連のビュークラス
"""
import logging
from django.views.generic import ListView
from django.core.exceptions import ObjectDoesNotExist
from base.models import Card, Category, Pack
from .base_views import BaseCardView

logger = logging.getLogger(__name__)


class PackDetailView(BaseCardView, ListView):
    """パックコレクションページのビュー（パックに含まれるカード一覧）"""

    model = Card
    template_name = 'pages/collection.html'
    paginate_by = 12

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack = None
        self.category = None

    def get_queryset(self):
        try:
            url_parameter = self.kwargs['identifier']

            # まずカテゴリーの series_code で検索
            try:
                self.category = Category.objects.get(series_code=url_parameter)
                queryset = Card.objects.filter(
                    is_published=True,
                    pack__category=self.category
                )
                self.pack = None
                logger.info(f"カテゴリー '{url_parameter}' でフィルタリング")
            except ObjectDoesNotExist:
                # カテゴリーが見つからない場合、パックの series_code で検索
                try:
                    self.pack = Pack.objects.get(series_code=url_parameter)
                    queryset = Card.objects.filter(
                        is_published=True,
                        pack=self.pack
                    )
                    self.category = None
                    logger.info(f"パック '{url_parameter}' でフィルタリング")
                except ObjectDoesNotExist:
                    logger.error(f"カテゴリーまたはパックが見つかりません: {url_parameter}")
                    return Card.objects.none()

            # ソート機能
            sort_by = self.request.GET.get('sort', 'default')
            if sort_by == 'price_asc':
                queryset = queryset.order_by('price')
            elif sort_by == 'price_desc':
                queryset = queryset.order_by('-price')
            else:
                # デフォルト: パック順、番号順、名前順
                if self.pack:
                    queryset = queryset.order_by('number', 'name')
                else:
                    queryset = queryset.order_by(
                        'pack__series_code', 'number', 'name')

            return queryset
        except Exception as e:
            logger.error(f"クエリセット取得中にエラーが発生: {e}")
            return Card.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_categories_context())

        if self.pack:
            pack_name = getattr(self, "pack", None)
            context['title'] = f'Pack #{pack_name.name if pack_name else "Unknown"}'
            context['pack'] = pack_name
        else:
            category_name = getattr(self, "category", None)
            context['title'] = f'Category #{category_name.name if category_name else "Unknown"}'
            context['category'] = category_name

        # パンくずリストのデータを準備
        breadcrumb_items = self._prepare_breadcrumb_items(
            pack=self.pack,
            category=self.category
        )

        # 現在のソート順をコンテキストに追加
        current_sort = self.request.GET.get('sort', 'default')
        context['current_sort'] = current_sort
        context['is_price_asc'] = current_sort == 'price_asc'
        context['is_price_desc'] = current_sort == 'price_desc'
        context['collection_breadcrumb_items'] = breadcrumb_items

        return context
