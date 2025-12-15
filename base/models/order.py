from django.db import models
from django.contrib.auth import get_user_model
from base.utils import custom_timestamp_id


class Order(models.Model):
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
