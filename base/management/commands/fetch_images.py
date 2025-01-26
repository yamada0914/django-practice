"""
fetch_images.py

指定したURLから画像を取得し、Djangoモデルに登録するためのスクリプト。

使用例:
    python manage.py fetch_images "https://example.com"
"""

import os
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from base.views import Item
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Command(BaseCommand):
    help = '指定したURLから画像をダウンロードしてDjangoに登録します。'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='画像を取得する対象のURL')

    def handle(self, *args, **kwargs):
        url = kwargs['url']

        # Seleniumでブラウザを開き、ページを読み込む
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get(url)
            time.sleep(1)
            self.scroll_down(driver)

            # HTMLを取得
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 画像を取得
            images = [img for img in soup.find_all(
                'img', attrs={'lazy': 'loaded'}) if img.get('src')]

            if not images:
                self.stdout.write(self.style.WARNING(
                    "No lazy-loaded images found on the page."))
                return

            # 画像をダウンロード
            for img in images:
                img_url = img['src']
                img_name = img.get('alt', 'Unnamed Image')

                # フルURLに変換
                if not img_url.startswith('http'):
                    img_url = requests.compat.urljoin(url, img_url)

                save_path = self.get_image_save_path(img_url)

                # 画像をダウンロード
                try:
                    img_response = requests.get(img_url, stream=True)
                    img_response.raise_for_status()
                    with open(save_path, 'wb') as f:
                        for chunk in img_response:
                            f.write(chunk)
                except requests.exceptions.RequestException as e:
                    self.stderr.write(self.style.WARNING(
                        f"Failed to download image {img_url}: {e}"))
                    continue

                # Djangoモデルに画像を登録
                with open(save_path, 'rb') as f:
                    Item.objects.create(
                        name=img_name, image=save_path, is_published=True)

                self.stdout.write(self.style.SUCCESS(
                    f"Downloaded and saved image: {img_name}"))

            self.stdout.write(self.style.SUCCESS("全ての画像を登録しました。"))

        finally:
            driver.quit()

    def get_image_save_path(self, img_url, base_dir='static/items') -> str:
        """画像の保存先パスを生成"""
        img_filename = os.path.basename(img_url)
        return os.path.join(base_dir, img_filename)

    # https://solomaker.club/how-to-handle-scroll-action-selenium/
    def scroll_down(self, driver):
        # ページの高さを取得
        height = driver.execute_script("return document.body.scrollHeight")
        # 最後までスクロールすると長いので、半分の長さに割る。
        height = height // 2

        # ループ処理で少しづつ移動
        for x in range(1, height):
            driver.execute_script("window.scrollTo(0, "+str(x)+");")
