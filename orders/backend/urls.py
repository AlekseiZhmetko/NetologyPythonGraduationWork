from django.urls import path
from .views import ImportDataFromYAML

urlpatterns = [

    path('import_yaml/', ImportDataFromYAML.as_view(), name='import_yaml'),

]