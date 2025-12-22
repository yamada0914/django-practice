"""
決済関連のビュークラス
"""
import json
import logging
from django.shortcuts import redirect
from django.views.generic import View, TemplateView
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
import stripe
from base.models import Card, Order
from base.utils import clear_cart

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_API_SECRET_KEY


class PaySuccessView(LoginRequiredMixin, TemplateView):
    """決済成功時のビュー"""
    template_name = 'pages/success.html'

    def get(self, request, *args, **kwargs):
        order_id = request.GET.get('order_id')

        if not order_id:
            logger.warning(f"注文IDが指定されていません: {request.user}")
            return redirect('/pages/orders-history/')

        order = self._get_order(request.user, order_id)
        if not order:
            return redirect('/pages/orders-history/')

        if order.is_confirmed:
            logger.info(f"注文は既に確定済みです: {order_id}")
            return redirect('/pages/orders-history/')

        if order.confirm():
            logger.info(f"注文を確定しました: {order_id}")

        # カート情報削除
        clear_cart(request)

        return super().get(request, *args, **kwargs)

    def _get_order(self, user, order_id):
        """注文を取得"""
        try:
            return Order.objects.get(user=user, id=order_id)
        except ObjectDoesNotExist:
            logger.error(f"注文が見つかりません: {order_id} (user: {user})")
            return None
        except Exception as e:
            logger.error(f"注文取得中にエラーが発生: {e}")
            return None


class PayCancelView(LoginRequiredMixin, TemplateView):
    """決済キャンセル時のビュー"""
    template_name = 'pages/cancel.html'

    def get(self, request, *args, **kwargs):
        # 最新の未確定注文を取得
        latest_order = Order.objects.filter(
            user=request.user, is_confirmed=False
        ).order_by('-created_at').first()

        if latest_order:
            try:
                items_data = latest_order.items

                # 在庫数と販売数を元の状態に戻す
                if items_data:
                    for item_data in items_data:
                        try:
                            item = Card.objects.get(pk=item_data['pk'])
                            quantity = item_data.get('quantity', 0)
                            item.sold_count = max(
                                0, item.sold_count - quantity)
                            item.stock += quantity
                            item.save()
                        except (ObjectDoesNotExist, KeyError) as e:
                            logger.error(
                                f"カードの復元に失敗: {item_data.get('pk', 'unknown')} - {e}")

            except (TypeError, AttributeError) as e:
                logger.error(f"注文データの処理に失敗: {latest_order.id} - {e}")

        # 全ての未確定注文を削除（データベースのクリーンアップ）
        orders = Order.objects.filter(user=request.user, is_confirmed=False)
        deleted_count = orders.count()
        if deleted_count > 0:
            orders.delete()
            logger.info(f"仮注文を{deleted_count}件削除しました")

        return super().get(request, *args, **kwargs)


def create_line_item(price: int, name: str, quantity: int) -> dict:
    """Stripe の line_item を作成"""
    if not settings.STRIPE_TAX_RATE_ID:
        raise ValueError(
            "STRIPE_TAX_RATE_ID が設定されていません。"
            "Stripe ダッシュボードで TaxRate を作成し、環境変数に設定してください。"
        )
    return {
        'price_data': {
            'currency': 'jpy',
            'unit_amount': price,
            'product_data': {'name': name},
        },
        'quantity': quantity,
        'tax_rates': [settings.STRIPE_TAX_RATE_ID],
    }


def check_profile_filled(profile) -> bool:
    """プロフィールの必須項目がすべて入力されているかチェック"""
    required_fields = ['name', 'zipcode', 'prefecture', 'city', 'address1']
    return all(getattr(profile, field, None) for field in required_fields)


class PayWithStripe(LoginRequiredMixin, View):
    """Stripe 決済処理ビュー"""

    def post(self, request, *args, **kwargs):
        # プロフィールが埋まっているかチェック
        if not check_profile_filled(request.user.profile):
            logger.warning(f"プロフィールが未入力: {request.user}")
            return redirect('/profile/')

        cart = request.session.get('cart')
        if not cart or not cart.get('items'):
            logger.warning(f"カートが空です: {request.user}")
            return redirect('/')

        items = []
        line_items = []

        try:
            for item_pk, quantity in cart['items'].items():
                try:
                    item = Card.objects.get(pk=item_pk, is_published=True)

                    # 在庫チェック
                    if item.stock < quantity:
                        logger.warning(
                            f"在庫不足: {item.name} (在庫: {item.stock}, 注文数: {quantity})")
                        return redirect('/cart/')

                    # Stripe 用の line_item を作成
                    line_item = create_line_item(
                        item.price, item.name, quantity)
                    line_items.append(line_item)

                    # Order モデル用のデータ
                    items.append({
                        "pk": item.pk,
                        "name": item.name,
                        "image": str(item.image) if item.image else '',
                        "price": item.price,
                        "quantity": quantity,
                    })

                    item.stock -= quantity
                    item.sold_count += quantity
                    item.save()

                except ObjectDoesNotExist:
                    logger.error(f"カードが見つかりません: {item_pk}")
                    continue

            if not items:
                logger.warning("有効なアイテムがありません")
                return redirect('/cart/')

            # 仮注文を作成
            tax_included_amount = int(cart['total'] * (settings.TAX_RATE + 1))

            # 配送先情報を辞書として抽出
            shipping_data = model_to_dict(
                request.user.profile,
                fields=['name', 'zipcode', 'prefecture',
                        'city', 'address1', 'address2', 'tel']
            )

            order = Order.objects.create(
                user=request.user,
                uid=request.user.pk,
                items=items,
                shipping=shipping_data,
                amount=cart['total'],
                tax_included=tax_included_amount
            )

            # Stripe Checkoutセッションを作成
            checkout_session = stripe.checkout.Session.create(
                customer_email=request.user.email,
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=f'{settings.MY_URL}/pay/success/?order_id={order.pk}',
                cancel_url=f'{settings.MY_URL}/pay/cancel/',
            )

            logger.info(f"決済セッションを作成: {order.id}")
            return redirect(checkout_session.url)

        except Exception as e:
            logger.error(f"決済処理中にエラーが発生: {e}")
            return redirect('/cart/')
