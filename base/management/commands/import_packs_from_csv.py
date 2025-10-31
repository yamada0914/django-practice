from django.core.management.base import BaseCommand
from base.models import Pack, Category
import csv
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'CSVファイルからPack（拡張パック）データを一括登録します'

    def handle(self, *args, **options):
        csv_path = os.path.join(
            settings.BASE_DIR, 'data/csv', 'packs_bulk.csv')
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(
                f'CSV ファイルが見つかりません: {csv_path}'))
            return

        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # カテゴリ取得
                category = None
                if row['category_slug']:
                    category = Category.objects.filter(
                        series_code=row['category_slug']).first()
                    if not category:
                        self.stdout.write(self.style.WARNING(
                            f"カテゴリが見つかりません: {row['category_slug']}（パック: {row['name']}）"))
                        continue
                # パック作成
                pack, created = Pack.objects.get_or_create(
                    slug=row['slug'],
                    defaults={
                        'name': row['name'],
                        'category': category,
                        'series_code': row.get('series_code', '').strip(),
                    }
                )
                if created:
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f"登録: {pack.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"既に存在: {pack.name}"))
            self.stdout.write(self.style.SUCCESS(f"\n合計{count}件のパックを登録しました。"))
