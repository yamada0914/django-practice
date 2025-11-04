"""
パックデータ一括登録コマンド

サンプルコマンド:
    # 通常実行（デフォルトCSVファイル）
    python manage.py load_packs

    # 別のCSVファイルを指定
    python manage.py load_packs --file data/csv/other_packs.csv

    # ドライラン（確認のみ、実際の更新は行わない）
    python manage.py load_packs --dry-run

    # ドライラン + 別ファイル
    python manage.py load_packs --file data/csv/test_packs.csv --dry-run

CSVファイル形式:
    name,slug,category_slug,series_code
    拡張パック「ブラックボルト」,black-bolt,sv,sv11b
    拡張パック「ホワイトフレア」,white-flare,sv,sv11w
"""

from django.core.management.base import BaseCommand
from base.models import Category, Pack
from typing import Dict, Tuple, Optional, Sequence
import csv
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# 定数定義
DEFAULT_CSV_PATH = 'data/csv/packs_bulk.csv'
REQUIRED_FIELDS = ['name', 'slug', 'category_slug']
OPTIONAL_FIELDS = ['series_code']


class Command(BaseCommand):
    help = 'CSVファイルからパックデータを一括登録します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=DEFAULT_CSV_PATH,
            help='CSVファイルのパス'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際のデータベース更新を行わず、処理内容のみ表示'
        )

    def handle(self, *args, **options):
        """メイン処理"""
        csv_path = os.path.join(settings.BASE_DIR, options['file'])

        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f'CSVファイルが見つかりません: {csv_path}')
            )
            return

        stats = self._process_csv_file(csv_path, options['dry_run'])
        self._display_results(stats, options['dry_run'])

    def _process_csv_file(self, csv_path: str, dry_run: bool) -> Dict[str, int]:
        """CSVファイルを処理してパックデータを登録"""
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        try:
            with open(csv_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)

                if not self._validate_csv_headers(reader.fieldnames):
                    stats['errors'] += 1
                    return stats

                for row_num, row in enumerate(reader, start=2):  # ヘッダーをのぞいて 2 段目から
                    result = self._process_row(row, row_num, dry_run)
                    stats[result] += 1

        except Exception as e:
            logger.error(f"CSVファイル処理中にエラーが発生: {e}")
            self.stdout.write(
                self.style.ERROR(f'CSVファイルの処理中にエラーが発生しました: {e}')
            )
            stats['errors'] += 1

        return stats

    def _validate_csv_headers(self, fieldnames: Optional[Sequence[str]]) -> bool:
        """CSVヘッダーの検証"""
        if not fieldnames:
            self.stdout.write(
                self.style.ERROR('CSVファイルにヘッダーがありません')
            )
            return False

        missing_fields = set(REQUIRED_FIELDS) - set(fieldnames)
        if missing_fields:
            self.stdout.write(
                self.style.ERROR(f'必要なフィールドが不足しています: {missing_fields}')
            )
            return False

        return True

    def _process_row(self, row: Dict[str, str], row_num: int, dry_run: bool) -> str:
        """CSVの1行を処理"""
        try:
            # データの正規化
            name = row['name'].strip()
            slug = row['slug'].strip()
            category_slug = row['category_slug'].strip()
            series_code = row.get('series_code', '').strip()

            # 必須フィールドの検証
            if not all([name, slug, category_slug]):
                self.stdout.write(
                    self.style.WARNING(f'行{row_num}: 必須フィールドが空です')
                )
                return 'skipped'

            # カテゴリーの取得（series_codeで検索）
            try:
                category = Category.objects.get(series_code=category_slug)
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'行{row_num}: カテゴリーが見つかりません: {category_slug}'
                    )
                )
                return 'skipped'

            # パックの作成または更新
            if dry_run:
                # 既存チェック（dry-runでは実際の更新は行わない）
                existing = Pack.objects.filter(slug=slug).exists()
                action = '更新' if existing else '作成'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'行{row_num}: パックを{action}します: {name} ({series_code})')
                )
                return 'created' if not existing else 'updated'

            try:
                pack, created = Pack.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'category': category,
                        'series_code': series_code
                    }
                )

                action = 'created' if created else 'updated'
                message = f'パックを作成しました' if created else f'パックを更新しました'

                self.stdout.write(
                    self.style.SUCCESS(
                        f'行{row_num}: {message}: {name} ({series_code})')
                )

                return action

            except Exception as e:
                logger.error(f"パック作成/更新中にエラー: {e}")
                self.stdout.write(
                    self.style.ERROR(f'行{row_num}: パックの作成/更新に失敗: {e}')
                )
                return 'errors'

        except Exception as e:
            logger.error(f"行{row_num}の処理中にエラー: {e}")
            self.stdout.write(
                self.style.ERROR(f'行{row_num}の処理中にエラーが発生: {e}')
            )
            return 'errors'

    def _display_results(self, stats: Dict[str, int], dry_run: bool) -> None:
        """処理結果を表示"""
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('ドライラン完了 - 実際のデータベース更新は行われませんでした')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'パックデータの登録が完了しました。'
                f'作成: {stats["created"]}件, '
                f'更新: {stats["updated"]}件, '
                f'スキップ: {stats["skipped"]}件, '
                f'エラー: {stats["errors"]}件'
            )
        )
