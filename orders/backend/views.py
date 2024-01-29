
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
from django.db.models import Q
# from django.contrib.auth.forms import AuthenticationForm
# from django.shortcuts import render, redirect
#
# from .forms import UserRegistrationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .serializers import ShopSerializer, CategorySerializer, ProductInfoSerializer, UserSerializer

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
    """
    Информация о текущем пользователе
    """
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


