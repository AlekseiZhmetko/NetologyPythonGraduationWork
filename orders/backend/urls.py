from django.urls import path
from . import views

urlpatterns = [

    path('import_yaml/', views.ImportDataFromYAML.as_view(), name='import_yaml'),
    path('register/', views.register, name='register'),
    path('login/', views.login_request, name='login'),
    path('', views.index, name='index')

]