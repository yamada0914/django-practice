from django.contrib import admin
from django.urls import path
from base import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Account
    path('account/login/', views.Login.as_view()),
    path('account/logout/', LogoutView.as_view()),
    path('account/signup/', views.SignUpView.as_view()),
    path('account/', views.AccountUpdateView.as_view()),
    path('profile/', views.ProfileUpdateView.as_view()),

    # Pay
    path('pay/checkout/', views.PayWithStripe.as_view()),
    path('pay/success/', views.PaySuccessView.as_view()),
    path('pay/cancel/', views.PayCancelView.as_view()),

    # Cart
    path('cart/remove/<str:pk>/', views.RemoveFromCartView.as_view()),
    path('cart/add/', views.AddCartView.as_view()),
    path('cart/', views.CartListView.as_view()),  # カートページ

    # Cards
    path('products/<str:pk>/', views.CardDetailView.as_view()),
    path('collections/<str:identifier>/', views.PackDetailView.as_view()),
    path('tags/<str:pk>/', views.TagListView.as_view()),

    path('', views.IndexListView.as_view()),  # トップページ

    # Pages
    path('pages/orders-history/<str:pk>/', views.OrderDetailView.as_view()),
    path('pages/orders-history/', views.OrderIndexView.as_view()),
    path('pages/help/', views.HelpView.as_view()),

]

# 開発環境でのメディアファイル配信設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
