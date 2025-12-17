"""
カート関連のビュークラス
"""
import logging
from django.shortcuts import redirect
from django.conf import settings
from django.views.generic import View, ListView
from django.core.exceptions import ObjectDoesNotExist
from base.models import Card
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CartListView(ListView):
    """カート一覧ビュー"""
    model = Card
    template_name = 'pages/cart.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total = 0

    def _get_cart_from_session(self) -> dict:
        """セッションからカートを取得"""
        return self.request.session.get('cart', {})

    def _is_cart_empty(self, cart: dict) -> bool:
        """カートが空かどうかをチェック"""
        return not cart or not cart.get('items')

    def _build_cart_items(self, cart: dict) -> list:
        """カートアイテムを構築して queryset を作成"""
        queryset = []
        for item_pk, quantity in cart.get('items', {}).items():
            try:
                obj = Card.objects.get(pk=item_pk, is_published=True)
                obj.quantity = quantity
                obj.subtotal = int(obj.price * quantity)
                queryset.append(obj)
                self.total += obj.subtotal
            except ObjectDoesNotExist:
                logger.warning(f"カート内のカードが見つかりません: {item_pk}")
                continue
        return queryset

    def _calculate_totals(self, cart: dict) -> None:
        """合計金額を計算してセッションに保存"""
        cart['total'] = self.total
        self.request.session['cart'] = cart

    def get_queryset(self):
        cart = self._get_cart_from_session()
        self.total = 0

        if self._is_cart_empty(cart):
            return []

        queryset = self._build_cart_items(cart)
        self._calculate_totals(cart)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total"] = self.total
        context["quantity_range"] = list(range(1, 21))
        # 送料無料までの残り金額
        context["remaining_for_free_shipping"] = max(
            0, settings.FREE_SHIPPING_THRESHOLD - self.total)
        return context


class AddCartView(View):
    """カートにアイテムを追加するビュー"""

    def _get_or_create_cart(self, request) -> dict:
        """カートを取得または作成"""
        cart = request.session.get('cart')
        if not cart or not cart.get('items'):
            cart = {'items': OrderedDict()}
        return cart

    def _update_cart_item(self, cart: dict, item_pk: str, quantity: int, update: bool) -> None:
        """カートアイテムを更新"""
        if update and item_pk in cart['items']:
            cart['items'][item_pk] = quantity
        elif item_pk in cart['items']:
            cart['items'][item_pk] += quantity
        else:
            cart['items'][item_pk] = quantity

    def post(self, request):
        item_pk = request.POST.get('item_pk')
        if not item_pk:
            logger.warning("item_pkが指定されていません")
            return redirect('/cart/')

        try:
            quantity = int(request.POST.get('quantity', 1))
            update = request.POST.get('update', 'false').lower() == 'true'
            operation = request.POST.get('operation')

            cart = self._get_or_create_cart(request)

            # 増減ボタンの処理
            if operation == 'increase' and item_pk in cart.get('items', {}):
                current_qty = cart['items'][item_pk]
                max_stock = int(request.POST.get('max_stock', 999))
                cart['items'][item_pk] = min(current_qty + 1, max_stock)
            elif operation == 'decrease' and item_pk in cart.get('items', {}):
                current_qty = cart['items'][item_pk]
                cart['items'][item_pk] = max(current_qty - 1, 1)
            else:
                # 通常の更新処理
                self._update_cart_item(cart, item_pk, quantity, update)

            request.session['cart'] = cart
            logger.info(f"カートを更新しました: {item_pk}")

        except (ValueError, TypeError) as e:
            logger.error(f"カート更新処理中にエラーが発生: {e}")

        return redirect('/cart/')


class RemoveFromCartView(View):
    """カートからアイテムを削除するビュー"""

    def post(self, request, pk):
        cart = request.session.get('cart')
        if cart and pk in cart.get('items', {}):
            del cart['items'][pk]
            request.session['cart'] = cart
            logger.info(f"カートからアイテムを削除しました: {pk}")
        return redirect('/cart/')
