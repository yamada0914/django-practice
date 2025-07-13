"""
create_categories.py

CSV からカテゴリを一括登録する Django 管理コマンド。

使用例:
    python manage.py create_categories
"""

import csv
import os
from django.core.management.base import BaseCommand
from base.models.item_models import Category
from django.conf import settings


class Command(BaseCommand):
    help = 'カテゴリを一括登録します。'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(settings.BASE_DIR, 'data/csv/categories.csv')
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['name']
                slug = row['slug']
                _, created = Category.objects.get_or_create(
                    name=name, slug=slug)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"作成: {name} ({slug})"))
                else:
                    self.stdout.write(f"既存: {name} ({slug})")
