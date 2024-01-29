from django.urls import path, include
from . import views
# from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

urlpatterns = [

    path('partner/import_yaml/', views.ImportDataFromYAML.as_view(), name='import_yaml'),
    path('users/register/', views.AccountRegistration.as_view(), name='register'),
    path('users/login/', views.LoginAccount.as_view(), name='login'),
    path('users/details/', views.AccountDetails.as_view(), name='account_details'),
    path('users/current/', views.CurrentUserView.as_view(), name='current_user'),
    path('users/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    # path('users/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),

    path('categories/', views.CategoryView.as_view(), name='categories'),
    path('shops/', views.ShopView.as_view(), name='shops'),
    # path('products/', views.ProductsView.as_view(), name='product_info'),
    path('products/', views.ProductInfoView.as_view(), name='products_info')

    # path('', views.index, name='index')

    ]
