"""
アプリケーション全体で使用される定数定義
"""
import os

# ID 生成関連の定数
ID_LENGTH = 22  # ランダム ID の文字数

# スライダー関連の定数
SLIDER_ITEMS_PER_GROUP = 3
MAX_POPULAR_CARDS = 12
MAX_RECENT_CARDS = 12
RECENT_CARDS_SESSION_KEY = 'recent_cards'

# ファイルパス
BANNER_CSV_PATH = os.path.join('data', 'csv', 'banners.csv')

# バナー設定
FOUR_BANNERS_CONFIG = [
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2supB.webp",
        "url": "#"
    },
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2211_hare2oripa.webp",
        "url": "#"
    },
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2deckB.webp",
        "url": "#"
    },
    {
        "src": "https://hareruya2-filepool.s3.amazonaws.com/banner/webp/4column/img_2209_hare2tumeB.webp",
        "url": "#"
    },
]
