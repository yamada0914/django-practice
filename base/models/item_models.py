from django.db import models
from django.utils.crypto import get_random_string
import os


def create_id() -> str:
    return get_random_string(22)


def upload_image_to(instance, filename):
    item_id = instance.id
    return os.path.join('static', 'items', item_id, filename)


class Tag(models.Model):
    slug = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Category(models.Model):
    slug = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Pack(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='packs')

    def __str__(self):
        return self.name


class Card(models.Model):
    id = models.CharField(default=create_id, primary_key=True,
                          max_length=22, editable=False)
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
