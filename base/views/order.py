"""
注文関連のビュークラス
"""
import json
import logging
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from base.models import Order

logger = logging.getLogger(__name__)


class OrderIndexView(LoginRequiredMixin, ListView):
    """注文一覧ビュー"""
    model = Order
    template_name = 'pages/orders.html'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    """注文詳細ビュー"""
    model = Order
    template_name = 'pages/order.html'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        # JSON データをパース
        try:
            context["items"] = json.loads(obj.items) if isinstance(
                obj.items, str) else obj.items
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"注文アイテムの JSON 解析に失敗: {obj.id} - {e}")
            context["items"] = []

        try:
            # JSONField は既に辞書として保存されているので、そのまま使用
            context["shipping"] = obj.shipping if isinstance(
                obj.shipping, dict) else {}
        except (TypeError, AttributeError) as e:
            logger.error(f"配送情報の取得に失敗: {obj.id} - {e}")
            context["shipping"] = {}

        return context
