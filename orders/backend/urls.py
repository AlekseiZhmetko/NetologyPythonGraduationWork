from django.urls import path
from . import views
urlpatterns = [

    path('partner/import_yaml/', views.ImportDataFromYAML.as_view(), name='import_yaml'),
    path('user/register/', views.AccountRegistration.as_view(), name='register'),
    path('user/login/', views.LoginAccount.as_view(), name='login'),
    # path('user/login/', views.login_request, name='login'),

    path('categories/', views.CategoryView.as_view(), name='categories'),
    path('shops/', views.ShopView.as_view(), name='shops'),
    path('products/', views.ProductsView.as_view(), name='product_info'),

    # path('', views.index, name='index')

    ]
