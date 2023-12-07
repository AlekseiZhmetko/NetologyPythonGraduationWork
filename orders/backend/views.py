# from django.shortcuts import render
# from rest_framework.views import APIView
# from yaml import load as load_yaml, Loader

from .models import Shop, Category, Product, ProductInfo, ProductParameter, Parameter, Contact, Order, OrderItem

from rest_framework.views import APIView
import yaml
from django.http import HttpResponse, JsonResponse

class ImportDataFromYAML(APIView):

    def get(self, request, *args, **kwargs):
        # указать не абсолютный путь файла
        yaml_file_path = r'C:\Users\Алексей\Desktop\PythonFinalDiplom\NetologyPythonGraduationWork\data\shop1.yaml'

        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

            shop, _ = Shop.objects.get_or_create(name=data['shop'])
            # print(shop)
            # print(f'New shop created with ID: {shop.id}')

            for category in data['categories']:
                category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                print(category_object)
                category_object.shops.add(shop.id)
                category_object.save()
            ProductInfo.objects.filter(shop_id=shop.id).delete()
            for item in data['goods']:
                product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                product_info = ProductInfo.objects.create(product_id=product.id,
                                                          external_id=item['id'],
                                                          model=item['model'],
                                                          price=item['price'],
                                                          price_rrc=item['price_rrc'],
                                                          quantity=item['quantity'],
                                                          shop_id=shop.id)
                for name, value in item['parameters'].items():
                    parameter_object, _ = Parameter.objects.get_or_create(name=name)
                    ProductParameter.objects.create(product_info_id=product_info.id,
                                                    parameter_id=parameter_object.id,
                                                    value=value)

            return JsonResponse({'Status': True})
