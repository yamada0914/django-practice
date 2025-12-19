"""
アカウント関連のビュークラス
"""
import logging
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect
from base.models import Profile
from base.forms import UserCreationForm, ProfileForm, AccountUpdateForm

logger = logging.getLogger(__name__)


class SignUpView(CreateView):
    """ユーザー登録ビュー"""
    form_class = UserCreationForm
    success_url = '/'
    template_name = 'pages/signup.html'

    def form_valid(self, form):
        user = form.save()

        # Profile 情報を保存
        profile = user.profile
        profile.last_name = self.request.POST.get('last_name', '')
        profile.first_name = self.request.POST.get('first_name', '')
        profile.last_name_kana = self.request.POST.get('last_name_kana', '')
        profile.first_name_kana = self.request.POST.get('first_name_kana', '')
        profile.company = self.request.POST.get('company', '')
        profile.tel = self.request.POST.get('tel', '')
        # 姓と名を結合して name に保存
        profile.name = f"{profile.last_name} {profile.first_name}".strip()
        profile.save()

        # 自動ログイン
        login(self.request, user)
        logger.info(f"新規ユーザー登録: {user.email}")

        return redirect('/')


class Login(LoginView):
    """ログインビュー"""
    template_name = 'pages/login_signup.html'


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """アカウント更新ビュー"""
    model = get_user_model()
    form_class = AccountUpdateForm
    template_name = 'pages/account.html'
    success_url = '/account/'

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        user = form.save()

        # プロフィール情報の更新（points は除外）
        profile = self.request.user.profile
        profile.name = self.request.POST.get('name', profile.name)
        profile.zipcode = self.request.POST.get('zipcode', profile.zipcode)
        profile.prefecture = self.request.POST.get(
            'prefecture', profile.prefecture)
        profile.city = self.request.POST.get('city', profile.city)
        profile.address1 = self.request.POST.get('address1', profile.address1)
        profile.address2 = self.request.POST.get('address2', profile.address2)
        profile.tel = self.request.POST.get('tel', profile.tel)
        # points は直接 POST から取得しない（セキュリティ上の理由）
        profile.save()

        logger.info(f"アカウント情報を更新: {user.email}")
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """プロフィール更新ビュー"""
    model = Profile
    form_class = ProfileForm
    template_name = 'pages/profile.html'
    success_url = '/profile/'

    def get_object(self):
        return self.request.user.profile
