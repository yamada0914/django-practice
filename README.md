# Django Practice - ポケモンカード通販サイト

ポケモンカードゲーム専門店「HARERUYA2」風の EC サイトを Django で構築したプロジェクトです。

## 🎯 プロジェクト概要

ポケモンカードの商品管理・通販機能を持つ Web アプリケーションです。

### 主な機能

- **カード一覧・詳細表示**: ポケモンカードの閲覧・検索
- **コレクション機能**: パック・カテゴリー別のカード一覧
- **ショッピングカート**: カードをカートに追加
- **注文管理**: 注文履歴の確認
- **決済機能**: Stripe を利用した決済処理
- **アカウント管理**: ユーザー登録・ログイン・プロフィール管理

## 📁 プロジェクト構造

```
django-practice/
├── base/                    # メインアプリケーション
│   ├── models/             # データモデル
│   │   ├── account.py      # アカウントモデル
│   │   ├── item_models.py  # カード・パック・カテゴリーモデル
│   │   └── order.py        # 注文モデル
│   ├── views/              # ビュークラス
│   │   ├── account.py      # アカウント関連ビュー
│   │   ├── base.py         # ベースビュークラス
│   │   ├── card.py         # カード関連ビュー
│   │   ├── cart.py         # カート関連ビュー
│   │   ├── collection.py   # コレクション関連ビュー
│   │   ├── order.py        # 注文関連ビュー
│   │   └── pay.py          # 決済関連ビュー
│   ├── management/commands/ # 管理コマンド
│   │   ├── create_categories.py      # カテゴリー作成
│   │   ├── fetch_images.py           # 画像取得
│   │   ├── import_items_from_csv.py  # カード一括インポート
│   │   └── load_packs.py             # パック一括登録
│   ├── constants.py        # 定数定義
│   └── utils.py            # ユーティリティ関数
├── config/                 # プロジェクト設定
│   ├── settings.py         # Django設定
│   └── urls.py            # URLルーティング
├── templates/              # テンプレート
│   ├── pages/             # ページテンプレート
│   └── snippets/          # スニペット（ヘッダー、サイドバーなど）
├── static/                # 静的ファイル
│   ├── css/               # スタイルシート
│   ├── images/            # 画像ファイル
│   ├── items/             # カード画像（インポート元）
│   └── js/                # JavaScript
├── media/                 # メディアファイル（アップロード済み）
│   └── items/             # カード画像（保存先）
├── data/csv/              # CSVデータファイル
│   ├── banners.csv        # バナーデータ
│   ├── categories.csv     # カテゴリーデータ
│   ├── items_bulk.csv     # カード一括データ
│   ├── packs_bulk.csv     # パック一括データ
│   └── pokemon_mapping.csv # ポケモン画像マッピング
```

## 🚀 セットアップ

### 必要な環境

- Python 3.9+
- Django 3.2+å
- SQLite（開発環境）
  å

### インストール手順

1. **リポジトリのクローン**

   ```bash
   git clone https://github.com/yamada0914/django-practice.git
   cd django-practice
   ```

2. **仮想環境の作成と有効化**

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **依存パッケージのインストール**

   ```bash
   pip install -r requirements.txt
   ```

4. **データベースのマイグレーション**

   ```bash
   python manage.py migrate
   ```

5. **スーパーユーザーの作成**

   ```bash
   python manage.py createsuperuser
   ```

6. **開発サーバーの起動**

   ```bash
   python manage.py runserver
   ```

   ブラウザで `http://127.0.0.1:8000` にアクセス

## ✅ テスト（pytest）

1. 依存関係に `pytest` / `pytest-django` が含まれているので、初回のみ再度インストールしておきます。

   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. そのまま `pytest` を実行すると Django 設定（`config.settings`）が読み込まれ、DB を再利用したテストが走ります。

   ```bash
   pytest                    # すべてのテスト
   pytest base/tests -k db   # モジュール/キーワードを絞って実行
   ```

3. CLI から自動実行したい場合は、用意したスクリプトを叩くだけです。並び替えたいオプションは引数で渡せます。

   ```bash
   ./scripts/run_tests.sh             # 依存関係→pytest をまとめて実行
   ./scripts/run_tests.sh -q --ff     # 例: 失敗テストを優先表示
   ```

`pytest.ini` には以下を設定済みです：

- `DJANGO_SETTINGS_MODULE=config.settings`
- `pythonpath=.` でルートを解決
- `addopts=--reuse-db --nomigrations -v`
- Django 5.0 で削除予定の警告を非表示

## 📊 データのインポート

### カテゴリーの登録

```bash
python manage.py create_categories
```

- **ファイル**: `data/csv/categories.csv`

### パックの一括登録

```bash
# 通常実行
python manage.py load_packs

# 実行前の確認（dry-run）
python manage.py load_packs --dry-run

# 別の CSV ファイルを指定
python manage.py load_packs --file data/csv/other_packs.csv
```

- **ファイル**: `data/csv/packs_bulk.csv`（デフォルト）
- **オプション**:
  - `--file <path>`: 別のCSVファイルを指定
  - `--dry-run`: 実行前の確認（実際の更新は行わない）
- **機能**: CSVヘッダー検証、詳細なエラーハンドリング、統計情報

### カードの一括登録

```bash
python manage.py import_items_from_csv
```

- **ファイル**: `data/csv/items_bulk.csv`
- **機能**: 画像ファイルの自動マッピング、パックとの関連付け

### その他のコマンド

#### `fetch_images`

指定したURLから画像を取得して登録します。

## 🔧 主要な機能

### ビューの構造

- **IndexListView**: トップページ
- **CardDetailView**: カード詳細ページ
- **PackDetailView**: パック・カテゴリー別コレクションページ
- **CategoryListView**: カテゴリー別一覧
- **TagListView**: タグ別一覧
- **CartListView**: ショッピングカート
- **OrderIndexView**: 注文一覧
- **OrderDetailView**: 注文詳細
- **PayWithStripe**: Stripe決済処理
- **HelpView**: ヘルプページ

### 共通機能

- **パンくずリスト**: ページ階層の表示
- **スライダー**: 人気カード・おすすめカードの表示
- **サイドバー**: カテゴリー一覧

## 📝 モデル構造

### Card（カード）

- ポケモン情報（ID、名前、英語名）
- 価格・在庫
- 画像（ImageField）
- パックとの関連
- レアリティ・タイプ・番号・シリーズコード

### Pack（パック）

- パック名・シリーズコード
- カテゴリーとの関連

### Category（カテゴリー）

- カテゴリー名・シリーズコード
- 複数のパックを含む

### Order（注文）

- 注文情報・配送先
- 注文アイテム（JSON形式）

## 🔐 環境変数

`secrets/.env.dev`ファイルを作成して設定してください（ファイルが存在しない場合は作成が必要）：

```bash
# secrets/.env.dev の例
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
STRIPE_API_SECRET_KEY=your-stripe-api-key
MY_URL=http://127.0.0.1:8000
```

必要な環境変数：

- `SECRET_KEY`: Django秘密鍵
- `DEBUG`: デバッグモード（True/False）
- `ALLOWED_HOSTS`: 許可されたホストå
- `STRIPE_API_SECRET_KEY`: Stripe APIキー
- `MY_URL`: アプリケーションのURL

## 📚 参考情報

- Django公式ドキュメント: https://docs.djangoproject.com/
- Stripe API: https://stripe.com/docs/api

## 📄 ライセンス

このプロジェクトは学習・練習用です。
