
from .models import Shop, Category, Product, ProductInfo, ProductParameter, Parameter, Contact,\
    Order, OrderItem, ConfirmEmailToken


from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import update_last_login
import yaml
from django.http import JsonResponse
# from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.db.models import Q, Sum, F
# from django.contrib.auth.forms import AuthenticationForm
# from django.shortcuts import render, redirect
# from .forms import UserRegistrationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from ujson import loads as load_json
import json
from .serializers import ShopSerializer, CategorySerializer, ProductInfoSerializer, UserSerializer,\
    OrderItemSerializer, OrderSerializer, OrderItemCreateSerializer

User = get_user_model()


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


class AccountRegistration(APIView):

    # def get(self, request, *args, **kwargs):
    #     if request.method == 'POST':
    #
    #         user_form = UserRegistrationForm(request.POST)
    #         if user_form.is_valid():
    #             new_user = user_form.save(commit=False)
    #             new_user.set_password(user_form.cleaned_data['password'])
    #             new_user.save()
    #             return render(request, 'register_done.html', {'new_user': new_user})
    #     else:
    #         user_form = UserRegistrationForm()
    #     return render(request, 'register.html', {'user_form': user_form})

    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    # new_user_registered.send(sender=self.__class__, user_id=user.id)

                    return JsonResponse({'Status': True})
                else:

                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})
        x = type(request.data)
        return JsonResponse({'Status': False, 'Errors': '', 'a': str(x)})


class ConfirmAccount(APIView):
    def post(self, request, *args, **kwargs):

        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Wrong token or email'})

        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})


class LoginAccount(APIView):
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, email=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    # Обновляем поле last_login в БД, т.к. при работе через токен оно не обновляется автоматически
                    update_last_login(None, user)
                return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Authentication is not successful'})

        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})


class AccountDetails(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)


    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if 'password' in request.data:
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])

        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


# class LoginAccount(APIView):
#
#     def post(self, request, *args, **kwargs):
#         if request.method == 'POST':
#             form = AuthenticationForm(request, data=request.POST)
#             if form.is_valid():
#                 email = form.cleaned_data.get('email')
#                 password = form.cleaned_data.get('password')
#                 user = authenticate(email=email, password=password)
#                 if user is not None:
#                     login(request, user)
#                     messages.info(request, f'You are now logged in as {email}.')
#                 else:
#                     messages.error(request, "Invalid email or password.")
#             else:
#                 messages.error(request, 'Invalid email or password.')
#         form = AuthenticationForm()
#         return render(request=request, template_name='login.html', context={'login_form': form})


class ShopView(ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer

    def create(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.data.get('user')).update(type='shop')
        return super().create(request, *args, **kwargs)

class CategoryView(ListAPIView):
    queryset = Category.objects.filter()
    serializer_class = CategorySerializer


class ProductsView(ListAPIView):
    queryset = ProductInfo.objects.filter()
    serializer_class = ProductInfoSerializer


class ProductInfoView(ListAPIView):
    def get(self, request, *args, **kwargs):

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)
            # query = Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()


        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class CurrentUserView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class BasketView(APIView):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_list = request.data.get('items')
        if items_list:
            try:
                objects_created = 0
                new_order_created = False
                basket = None

                for order_item in items_list:
                    order_id = order_item.get('order_id', None)

                    if order_id is not None:
                        try:
                            basket, _ = Order.objects.get_or_create(id=order_id, user_id=request.user.id,
                                                                    status='basket')
                            order_item.update({'order': basket.id})
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                    else:
                        if not new_order_created:
                            # If order_id is not specified and a new order hasn't been created yet, create a new order
                            basket = Order.objects.create(user_id=request.user.id, status='basket')
                            new_order_created = True

                        order_item.update({'order': basket.id})

                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        serializer.save()
                        objects_created += 1
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': True, 'Создано объектов': objects_created})
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Invalid JSON format'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_list = request.data.get('items')
        if items_list:
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            query = Q()
            objects_deleted = False
            for order_item in items_list:
                order_item_id = order_item.get('id')
                # print(f"order_item_id: {order_item_id}")
                if order_item_id and str(order_item_id).isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                try:
                    deleted_count, _ = OrderItem.objects.filter(query).delete()
                except IntegrityError as error:
                    return JsonResponse({'Status': False, 'Errors': str(error)})
                else:
                    return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
            else:
                return JsonResponse({'Status': False, 'Errors': 'No valid order_item_id provided'})
        else:
            return JsonResponse({'Status': False, 'Errors': 'No items specified for deletion'})

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_list = request.data.get('items')
        if items_list:
            try:
                objects_updated = 0

                for order_item_data in items_list:
                    order_item_id = order_item_data.get('order_item_id', None)
                    order_id = order_item_data.get('order_id', None)

                    if order_item_id is not None and order_id is not None:
                        try:
                            order_item = OrderItem.objects.get(id=order_item_id, order_id=order_id,
                                                               order__user=request.user)
                        except OrderItem.DoesNotExist:
                            return JsonResponse({'Status': False,
                                                 'Errors': 'OrderItem not found for the user or order_id and order_item_id do not match'})

                        serializer = OrderItemSerializer(instance=order_item, data=order_item_data)
                        if serializer.is_valid():
                            serializer.save()
                            objects_updated += 1
                        else:
                            return JsonResponse({'Status': False, 'Errors': serializer.errors})
                    else:
                        return JsonResponse({'Status': False,
                                             'Errors': 'Both order_item_id and order_id must be specified for an item in PUT request'})

                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Invalid JSON format'})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderView(APIView):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        order = Order.objects.filter(
            user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        status='new')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        new_order.send(sender=self.__class__, user_id=request.user.id)
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})