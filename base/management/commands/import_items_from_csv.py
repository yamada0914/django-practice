from django.core.management.base import BaseCommand
from base.models import Card, Pack
from django.core.files import File
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

    def _get_search_directories(self):
        """検索対象ディレクトリのリストを取得"""
        static_items_dir = Path(settings.BASE_DIR) / 'static' / 'items'
        media_items_dir = Path(settings.MEDIA_ROOT) / 'items'
        search_dirs = [static_items_dir]
        if media_items_dir.exists():
            search_dirs.append(media_items_dir)
        return search_dirs

    def _search_file_in_directories(self, filename, search_dirs):
        """指定されたファイル名を検索ディレクトリ内で探す"""
        for search_dir in search_dirs:
            file_path = search_dir / filename
            if file_path.exists() and file_path.is_file():
                return file_path
        return None

    def _find_image_file(self, csv_image_path, pokemon_name=None):
        """CSVの画像パスからstatic/items/またはmedia/items/内のファイルを検索"""
        search_dirs = self._get_search_directories()

        if pokemon_name and pokemon_name in self.image_mapping:
            mapped_file = self._search_file_in_directories(
                self.image_mapping[pokemon_name], search_dirs
            )
            if mapped_file:
                return mapped_file

        if not csv_image_path:
            return None

        filename = os.path.basename(csv_image_path)
        file_path = self._search_file_in_directories(filename, search_dirs)
        if file_path:
            return file_path

        base_name = os.path.splitext(filename)[0]
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            file_path = self._search_file_in_directories(
                f"{base_name}{ext}", search_dirs)
            if file_path:
                return file_path

        if pokemon_name:
            self.stdout.write(self.style.WARNING(
                f"画像ファイルが見つかりません: {csv_image_path} (ポケモン: {pokemon_name})"
            ))
        return None

    def _get_pack(self, pack_series_code):
        """パックを取得"""
        if not pack_series_code:
            return None
        pack = Pack.objects.filter(series_code=pack_series_code).first()
        if not pack:
            self.stdout.write(self.style.WARNING(
                f"パックが見つかりません: {pack_series_code}"
            ))
        return pack

    def _create_or_update_card(self, row, pack):
        """カードを作成または更新"""
        return Card.objects.update_or_create(
            name=row['name'],
            defaults={
                'pokemon_name': row['pokemon_name'],
                'english_name': row['english_name'],
                'pokemon_id': row['pokemon_id'],
                'price': int(row['price']),
                'stock': int(row['stock']),
                'pack': pack,
                'rarity': row.get('rarity', '').strip(),
                'type': row.get('type', '').strip(),
                'number': row.get('number', '').strip(),
                'series_code': row.get('series_code', '').strip(),
                'is_published': True,
            }
        )

    def _save_card_image(self, item, row):
        """カードの画像を保存"""
        csv_image_path = row.get('image', '').strip()
        source_image_file = self._find_image_file(
            csv_image_path,
            pokemon_name=row.get('pokemon_name', '').strip()
        )

        if source_image_file:
            filename = os.path.basename(source_image_file.name)
            with open(source_image_file, 'rb') as f:
                item.image.save(filename, File(f), save=False)
            item.save()
        elif not item.image:
            self.stdout.write(self.style.WARNING(
                f"画像が見つかりません（画像なしで登録）: {item.name}"
            ))

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
                pack = self._get_pack(row.get('pack_series_code', '').strip())
                if not pack:
                    continue

                item, created = self._create_or_update_card(row, pack)
                self._save_card_image(item, row)

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
