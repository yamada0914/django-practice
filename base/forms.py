"""
フォームクラス定義
"""
from django import forms
from django.contrib.auth import get_user_model
from base.models import Profile


class UserCreationForm(forms.ModelForm):
    """ユーザー作成フォーム"""
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='パスワード'
    )

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """プロフィール更新フォーム"""

    class Meta:
        model = Profile
        fields = (
            'last_name', 'first_name', 'last_name_kana', 'first_name_kana',
            'company', 'name', 'zipcode', 'prefecture', 'city',
            'address1', 'address2', 'tel'
        )
        # pointsフィールドは除外（セキュリティ上の理由）

    def save(self, commit=True):
        profile = super().save(commit=False)
        # 姓と名を結合し name に保存
        if profile.last_name or profile.first_name:
            profile.name = f"{profile.last_name} {profile.first_name}".strip()
        if commit:
            profile.save()
        return profile


class AccountUpdateForm(forms.ModelForm):
    """アカウント更新フォーム"""

    class Meta:
        model = get_user_model()
        fields = ('username', 'email')
