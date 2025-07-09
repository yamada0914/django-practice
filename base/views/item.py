from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from base.models import Item, Category, Tag
import csv
import os
from django.conf import settings


class IndexListView(ListView):
    model = Item
    template_name = 'pages/index.html'
    queryset = Item.objects.filter(is_published=True)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['CATEGORIES'] = range(1, 13)
        # バナーCSV読み込み
        banners = []
        csv_path = os.path.join(settings.BASE_DIR, 'data/csv', 'banners.csv')
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                banners.append(row)
        context['BANNERS'] = banners
        # POPULAR_ITEMSを直接取得し 12 件だけ使い 3 件ずつグループ化して 4 ページ表示
        popular_items = list(Item.objects.filter(
            is_published=True).order_by('-sold_count')[:12])
        print('popular_items', popular_items)

        def batch(lst, n):
            return [lst[i:i+n] for i in range(0, len(lst), n)]
        context['POPULAR_GROUPS'] = batch(popular_items, 3)
        # 4 カラムバナー
        context['FOUR_BANNERS'] = [
            {"src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2supB.webp", "url": "#"},
            {"src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2211_hare2oripa.webp", "url": "#"},
            {"src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2deckB.webp", "url": "#"},
            {"src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2tumeB.webp", "url": "#"},
        ]
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = 'pages/item.html'


class CategoryListView(ListView):
    model = Item
    template_name = 'pages/list.html'
    paginate_by = 2

    def get_queryset(self):
        self.category = Category.objects.get(slug=self.kwargs['pk'])
        return Item.objects.filter(is_published=True, category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Category #{self.category.name}'
        return context


class TagListView(ListView):
    model = Item
    template_name = 'pages/list.html'
    paginate_by = 2

    def get_queryset(self):
        self.tag = Tag.objects.get(slug=self.kwargs['pk'])
        return Item.objects.filter(is_published=True, tags=self.tag)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Tag #{self.tag.name}"
        return context


class HelpView(TemplateView):
    template_name = 'pages/help.html'
