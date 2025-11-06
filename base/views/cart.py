from django.shortcuts import redirect
from django.conf import settings
from django.views.generic import View, ListView
from base.models import Card
from collections import OrderedDict


class CartListView(ListView):
    model = Card
    template_name = 'pages/cart.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total = 0
        self.tax_included_total = 0

    def _get_cart_from_session(self):
        """セッションからカートを取得"""
        return self.request.session.get('cart', None)

    def _is_cart_empty(self, cart):
        """カートが空かどうかをチェック"""
        return cart is None or len(cart.get('items', {})) == 0

    def _build_cart_items(self, cart):
        """カートアイテムを構築して queryset を作成"""
        queryset = []
        for item_pk, quantity in cart['items'].items():
            try:
                obj = Card.objects.get(pk=item_pk)
                obj.quantity = quantity
                obj.subtotal = int(obj.price * quantity)
                queryset.append(obj)
                self.total += obj.subtotal
            except Card.DoesNotExist:
                continue
        return queryset

    def _calculate_totals(self, cart):
        """合計金額を計算してセッションに保存"""
        self.tax_included_total = int(self.total * (settings.TAX_RATE + 1))
        cart['total'] = self.total
        cart['tax_included_total'] = self.tax_included_total
        self.request.session['cart'] = cart

    def get_queryset(self):
        cart = self._get_cart_from_session()
        self.total = 0
        self.tax_included_total = 0

        if self._is_cart_empty(cart):
            return []

        queryset = self._build_cart_items(cart)
        self._calculate_totals(cart)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total"] = self.total
        context["tax_included_total"] = self.tax_included_total
        context["quantity_range"] = list(range(1, 21))
        return context


class AddCartView(View):

    def _get_or_create_cart(self, request):
        """カートを取得または作成"""
        cart = request.session.get('cart', None)
        if cart is None or len(cart) == 0:
            cart = {'items': OrderedDict()}
        return cart

    def _update_cart_item(self, cart, item_pk, quantity, update):
        """カートアイテムを更新"""
        if update and item_pk in cart['items']:
            cart['items'][item_pk] = quantity
        elif item_pk in cart['items']:
            cart['items'][item_pk] += quantity
        else:
            cart['items'][item_pk] = quantity

    def post(self, request):
        item_pk = request.POST.get('item_pk')
        quantity = int(request.POST.get('quantity', 1))
        update = request.POST.get('update', 'false').lower() == 'true'

        cart = self._get_or_create_cart(request)
        self._update_cart_item(cart, item_pk, quantity, update)
        request.session['cart'] = cart

        return redirect('/cart/')


def remove_from_cart(request, pk):
    cart = request.session.get('cart', None)
    if cart is not None and pk in cart.get('items', {}):
        del cart['items'][pk]
        request.session['cart'] = cart
    return redirect('/cart/')
