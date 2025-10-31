from django.core.management.base import BaseCommand
from base.models import Card, Pack
import csv
import os
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = 'CSVファイルから商品データを一括登録します'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_mapping = {}
        self._load_image_mapping()

    def _load_image_mapping(self):
        """画像マッピングファイルを読み込む"""
        mapping_path = os.path.join(
            settings.BASE_DIR, 'data/csv', 'image_mapping.csv')

        if os.path.exists(mapping_path):
            try:
                with open(mapping_path, encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        pokemon_name = row.get('pokemon_name', '').strip()
                        image_filename = row.get('image_filename', '').strip()
                        if pokemon_name and image_filename:
                            self.image_mapping[pokemon_name] = image_filename
                self.stdout.write(self.style.SUCCESS(
                    f"画像マッピングを読み込みました: {len(self.image_mapping)}件"
                ))
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"画像マッピングファイルの読み込みに失敗: {e}"
                ))

    def _get_image_path(self, csv_image_path, pokemon_name=None):
        """CSVの画像パスをstatic/items/内の実際のファイルパスに変換"""
        static_items_dir = Path(settings.BASE_DIR) / 'static' / 'items'

        # 1. マッピングファイルでポケモン名から直接取得（最優先）
        if pokemon_name and pokemon_name in self.image_mapping:
            mapped_filename = self.image_mapping[pokemon_name]
            full_path = static_items_dir / mapped_filename
            if full_path.exists() and full_path.is_file():
                return f"static/items/{mapped_filename}"

        # 2. CSVの画像パスからファイル名を抽出して検索
        if csv_image_path:
            filename = os.path.basename(csv_image_path)

            # ファイル名がそのまま存在するか確認
            full_path = static_items_dir / filename
            if full_path.exists() and full_path.is_file():
                return f"static/items/{filename}"

            # 拡張子なしで検索
            base_name = os.path.splitext(filename)[0]
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                full_path = static_items_dir / f"{base_name}{ext}"
                if full_path.exists() and full_path.is_file():
                    return f"static/items/{full_path.name}"

        # 3. 見つからない場合
        if pokemon_name:
            self.stdout.write(self.style.WARNING(
                f"画像ファイルが見つかりません: {csv_image_path} (ポケモン: {pokemon_name})"
            ))
        return csv_image_path if csv_image_path else ''

    def handle(self, *args, **options):
        csv_path = os.path.join(
            settings.BASE_DIR, 'data/csv', 'items_bulk.csv')
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSVファイルが見つかりません: {csv_path}'))
            return

        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            created_count = 0
            updated_count = 0

            for row in reader:
                # パック取得または作成
                pack = None
                if row['pack_series_code']:
                    pack = Pack.objects.filter(
                        series_code=row['pack_series_code']).first()
                    if not pack:
                        self.stdout.write(self.style.WARNING(
                            f"パックが見つかりません: {row['pack_series_code']}（商品: {row['name']}）"))
                        continue

                # 新しいフィールドの値を取得（空の場合は空文字列）
                rarity = row.get('rarity', '').strip()
                card_type = row.get('type', '').strip()
                number = row.get('number', '').strip()
                series_code = row.get('series_code', '').strip()

                # 画像パスを変換（CSVのパス → static/items/内の実際のファイルパス）
                csv_image_path = row.get('image', '').strip()
                image_path = self._get_image_path(
                    csv_image_path,
                    pokemon_name=row.get('pokemon_name', '').strip()
                )

                # 商品作成または更新
                item, created = Card.objects.update_or_create(
                    name=row['name'],
                    defaults={
                        'pokemon_name': row['pokemon_name'],
                        'english_name': row['english_name'],
                        'pokemon_id': row['pokemon_id'],
                        'price': int(row['price']),
                        'stock': int(row['stock']),
                        'pack': pack,
                        'image': image_path,
                        'rarity': rarity,
                        'type': card_type,
                        'number': number,
                        'series_code': series_code,
                        'is_published': True,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"登録: {item.name}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"更新: {item.name}"))

            self.stdout.write(self.style.SUCCESS(
                f"\n合計{created_count + updated_count}件の商品を処理しました。"
                f"（新規登録: {created_count}件, 更新: {updated_count}件）"
            ))
