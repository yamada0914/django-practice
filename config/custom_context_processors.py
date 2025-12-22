from django.conf import settings
from base.models import Card


def base(request):
    items = Card.objects.filter(is_published=True)

    # ナビゲーションを非表示にするパス
    hide_navigation_paths = [
        '/account/',
        '/account/login',
        '/account/signup',
        '/cart',
        '/pages/orders-history',
    ]

    # 現在のパスが非表示対象かチェック
    show_navigation = not any(
        path in request.path for path in hide_navigation_paths
    )

    return {
        'TITLE': settings.TITLE,
        'ADDTIONAL_ITEMS': items,
        'POPULAR_ITEMS': items.order_by('-sold_count'),
        'show_navigation': show_navigation,
    }
