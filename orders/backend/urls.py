from django.urls import path
from . import views
urlpatterns = [

    path('partner/import_yaml/', views.ImportDataFromYAML.as_view(), name='import_yaml'),
    path('user/register/', views.AccountRegistration.as_view(), name='register'),
    # path('user/login/', views.login_request, name='login'),

    path('categories/', views.CategoryView.as_view(), name='categories'),
    path('shops/', views.ShopView.as_view(), name='shops'),
    path('products/', views.ProductsView.as_view(), name='product_info'),

    path('', views.index, name='index')

    ]
# urlpatterns = [
#     path('partner/update', ImportDataFromYAML.as_view(), name='partner-update'),
#     # path('partner/state', PartnerState.as_view(), name='partner-state'),
#     # path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
#     path('user/register', AccountRegistration.as_view(), name='user-register'),
#     # path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
#     # path('user/details', AccountDetails.as_view(), name='user-details'),
#     # path('user/contact', ContactView.as_view(), name='user-contact'),
#     # path('user/login', LoginAccount.as_view(), name='user-login'),
#     # path('user/password_reset', reset_password_request_token, name='password-reset'),
#     # path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
#     # path('categories', CategoryView.as_view(), name='categories'),
#     # path('shops', ShopView.as_view(), name='shops'),
#     # path('products', ProductInfoView.as_view(), name='shops'),
#     # path('basket', BasketView.as_view(), name='basket'),
#     # path('order', OrderView.as_view(), name='order'),
#
# ]