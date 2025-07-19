from django.conf import settings
from base.models import Card


def base(request):
    items = Card.objects.filter(is_published=True)
    return {
        'TITLE': settings.TITLE,
        'ADDTIONAL_ITEMS': items,
        'POPULAR_ITEMS': items.order_by('-sold_count')
    }
