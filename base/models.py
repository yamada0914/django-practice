"""
Django モデル定義
"""
import os
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth import get_user_model
from base.utils import create_id, custom_timestamp_id
from base.constants import ID_LENGTH


# ============================================================================
# ユーティリティ関数
# ============================================================================

def upload_image_to(instance, filename):
    """画像のアップロード先を決定"""
    return os.path.join('items', filename)


# ============================================================================
# アイテム関連モデル
# ============================================================================

class Tag(models.Model):
    """タグモデル"""
    slug = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Category(models.Model):
    """カテゴリーモデル"""
    series_code = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Pack(models.Model):
    """パックモデル"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='packs')
    series_code = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return self.name


class Card(models.Model):
    """カードモデル"""
    id = models.CharField(default=create_id, primary_key=True,
                          max_length=ID_LENGTH, editable=False)
    pokemon_id = models.CharField(default='', max_length=50)
    name = models.CharField(default='', max_length=100)
    pokemon_name = models.CharField(default='', max_length=50)
    english_name = models.CharField(default='', max_length=50)
    price = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(default='', blank=True)
    sold_count = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(default='', blank=True,
                              upload_to=upload_image_to)
    pack = models.ForeignKey(
        Pack, on_delete=models.SET_NULL, null=True, blank=True, related_name='cards')
    tags = models.ManyToManyField(Tag)
    rarity = models.CharField(
        max_length=10, blank=True, default='')
    type = models.CharField(max_length=10, blank=True, default='')
    number = models.CharField(
        max_length=20, blank=True, default='')  # 例: 001/100
    series_code = models.CharField(
        max_length=20, blank=True, default='')  # 例: SV9

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        """表示用の名前を生成"""
        parts = [self.name]
        if self.rarity:
            parts.append(f'({self.rarity})')
        if self.type:
            parts.append(f'{{{self.type}}}')
        if self.number:
            parts.append(f'〈{self.number}〉')
        if self.series_code:
            parts.append(f'[{self.series_code}]')
        return ''.join(parts)


# ============================================================================
# アカウント関連モデル
# ============================================================================

class UserManager(BaseUserManager):
    """カスタムユーザーマネージャー"""

    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(
            username,
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """カスタムユーザーモデル"""
    id = models.CharField(
        default=create_id, primary_key=True, max_length=ID_LENGTH)
    username = models.CharField(
        max_length=50, unique=True, blank=True, default='匿名')
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=0)
    objects = UserManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Profile(models.Model):
    """ユーザープロフィールモデル"""
    user = models.OneToOneField(
        User, primary_key=True, on_delete=models.CASCADE)
    # 名前関連
    last_name = models.CharField(
        default='', blank=True, max_length=50, verbose_name='姓')
    first_name = models.CharField(
        default='', blank=True, max_length=50, verbose_name='名')
    last_name_kana = models.CharField(
        default='', blank=True, max_length=50, verbose_name='姓（フリガナ）')
    first_name_kana = models.CharField(
        default='', blank=True, max_length=50, verbose_name='名（フリガナ）')
    company = models.CharField(
        default='', blank=True, max_length=100, verbose_name='会社名')
    # 既存フィールド
    name = models.CharField(default='', blank=True, max_length=50)
    zipcode = models.CharField(default='', blank=True, max_length=8)
    prefecture = models.CharField(default='', blank=True, max_length=50)
    city = models.CharField(default='', blank=True, max_length=50)
    address1 = models.CharField(default='', blank=True, max_length=50)
    address2 = models.CharField(default='', blank=True, max_length=50)
    tel = models.CharField(default='', blank=True, max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


# ============================================================================
# 注文関連モデル
# ============================================================================

class Order(models.Model):
    """注文モデル"""
    id = models.CharField(default=custom_timestamp_id,
                          editable=False, primary_key=True, max_length=50)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    uid = models.CharField(editable=False, max_length=50)
    is_confirmed = models.BooleanField(default=False)
    amount = models.PositiveIntegerField(default=0)
    tax_included = models.PositiveIntegerField(default=0)
    items = models.JSONField()
    shipping = models.JSONField()
    shipped_at = models.DateTimeField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)
    memo = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id

    def confirm(self):
        """注文を確定"""
        if self.is_confirmed:
            return False
        self.is_confirmed = True
        self.save()
        return True


# ============================================================================
# シグナル
# ============================================================================

@receiver(post_save, sender=User)
def create_onetoone(sender, **kwargs):
    """User作成時にProfileを自動生成"""
    if kwargs['created']:
        Profile.objects.create(user=kwargs['instance'])

