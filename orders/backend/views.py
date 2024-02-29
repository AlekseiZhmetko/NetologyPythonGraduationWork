import sentry_sdk
from django.shortcuts import render

from .models import Shop, Category, Product, ProductInfo, ProductParameter, Parameter, Contact, \
    Order, OrderItem, ConfirmEmailToken

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import update_last_login
# from .signals import new_order, new_user_registered, password_reset_token_created
from .tasks import send_test_email_task, new_order_task, new_user_registered_task, password_reset_token_created_task, \
    upload_avatar_task, upload_product_image
from yaml import load as load_yaml, Loader
import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from django.contrib.auth import login, authenticate
from django.db.models import Q, Sum, F
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from distutils.util import strtobool
from .serializers import ShopSerializer, CategorySerializer, ProductInfoSerializer, UserSerializer, \
    OrderItemSerializer, OrderSerializer, OrderItemCreateSerializer, ContactSerializer
from django_rest_passwordreset.views import ResetPasswordRequestToken
from django_rest_passwordreset.models import ResetPasswordToken
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.exceptions import ValidationError

User = get_user_model()


class PartnerImportDataFromYAML(APIView):
    """
    View for importing data from yaml file
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Shops only'}, status=403)

        url = request.data.get('url')

        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)}, status=400)
            else:
                stream = requests.get(url).content
                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)

                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()

                ProductInfo.objects.filter(shop_id=shop.id).delete()

                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                    if item.get('product_image'):
                        product_image_url = item.pop('product_image')
                        print(product_image_url)

                        product_info = ProductInfo.objects.create(
                            product=product,
                            external_id=item['id'],
                            model=item['model'],
                            price=item['price'],
                            price_rrc=item['price_rrc'],
                            quantity=item['quantity'],
                            shop_id=shop.id,
                            # product_image=ContentFile(response.content, name=filename),
                        )

                        upload_product_image.delay(product_info.id, product_image_url)

                        for name, value in item['parameters'].items():
                            parameter_object, _ = Parameter.objects.get_or_create(name=name)
                            ProductParameter.objects.create(product_info=product_info, parameter=parameter_object,
                                                            value=value)

                        else:
                            product_info = ProductInfo.objects.create(
                                product=product,
                                external_id=item['id'],
                                model=item['model'],
                                price=item['price'],
                                price_rrc=item['price_rrc'],
                                quantity=item['quantity'],
                                shop_id=shop.id,
                            )

                            for name, value in item['parameters'].items():
                                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                                ProductParameter.objects.create(product_info=product_info, parameter=parameter_object,
                                                                value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Error': 'Missing required URL in data'}, status=400)


# class PartnerImportDataFromYAML(APIView):
#     def post(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
#
#         if request.user.type != 'shop':
#             return JsonResponse({'Status': False, 'Error': 'Shops only'}, status=403)
#
#         url = request.data.get('url')
#
#         if url:
#             validate_url = URLValidator()
#             try:
#                 validate_url(url)
#             except ValidationError as e:
#                 return JsonResponse({'Status': False, 'Error': str(e)}, status=400)
#             else:
#                 stream = requests.get(url).content
#                 data = load_yaml(stream, Loader=Loader)
#
#                 shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
#
#                 for category in data['categories']:
#                     category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
#                     category_object.shops.add(shop.id)
#                     category_object.save()
#
#                 ProductInfo.objects.filter(shop_id=shop.id).delete()
#
#                 for item in data['goods']:
#                     product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
#                     # ProductInfo.objects.create(product=product, external_id=item['id'])
#
#                     print(item)
#                     print('ITS ID OF A PRODUCT', product.id)
#                     product_image_url = item.pop('product_image', None)
#                     item['external_id'] = item.pop('id')
#                     print(item['external_id'])
#                     item['product'] = product
#                     print('HERE', item['product'])
#                     print(item)
#                     print('NOW IT WOULD BE FIRE!!!')
#                     product_info_serializer = ProductInfoSerializer(data=item)
#                     print(product_info_serializer)
#                     if product_info_serializer.is_valid():
#                         product_info = product_info_serializer.save()
#                         print(product_info)
#                         product_info.save()
#                         return JsonResponse({'Status': True})
#                     else:
#                         return JsonResponse({'Status': False, 'Errors': product_info_serializer.errors}, status=400)
#
#                     product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
#                     product_image_url = item.get('product_image')
#                     print(product_image_url)
#                     if product_image_url:
#                         response = requests.get(product_image_url)
#
#                         if response.status_code == 200:
#                             filename = f'{product.id}_image.jpg'
#                             # print(filename)
#                             product_info = ProductInfo.objects.create(
#                                 product=product,
#                                 external_id=item['id'],
#                                 model=item['model'],
#                                 price=item['price'],
#                                 price_rrc=item['price_rrc'],
#                                 quantity=item['quantity'],
#                                 shop_id=shop.id,
#                                 product_image=ContentFile(response.content, name=filename),
#                             )


class AccountRegistration(APIView):
    """
    View for user registration
    """

    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            errors = {}

            try:
                validate_password(request.data['password'])
            except ValidationError as password_error:
                error_array = [str(error) for error in password_error]
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}}, status=400)

            avatar_url = request.data.pop('avatar', None)

            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()
                print(user.id)
                class_name = self.__class__.__name__
                upload_avatar_task.delay(user_id=user.id, avatar_url=avatar_url)
                new_user_registered_task.delay(user_id=user.id, sender_class=class_name)

                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': user_serializer.errors}, status=400)

        return JsonResponse({'Status': False, 'Errors': 'Missing required fields (email, password)'}, status=400)


class ConfirmAccount(APIView):
    """
    View for user account confirmation
    """

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
    """
    View for account login
    """

    def get(self, request):
        return render(request, 'login.html')


    def post(self, request, *args, **kwargs):
        try:
            if {'email', 'password'}.issubset(request.data):
                user = authenticate(request, email=request.data['email'], password=request.data['password'])
                print(user)
                if user is not None:
                    if user.is_active:
                        token, _ = Token.objects.get_or_create(user=user)
                        # Обновляем поле last_login в БД, т.к. при работе через токен оно не обновляется автоматически
                        update_last_login(None, user)
                    return JsonResponse({'Status': True, 'Token': token.key})

                return sentry_sdk.capture_message("Login unsuccessful. Sent to Sentry")
                # return JsonResponse({'Status': False, 'Errors': 'Authentication is not successful'})


            return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})


        except Exception as e:
            sentry_sdk.capture_exception(e)

class AccountDetails(APIView):
    """
    View for getting and updating user account details
    """

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
    """
    View for getting a list of shops or creating a new shop
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer

    def create(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.data.get('user')).update(type='shop')
        return super().create(request, *args, **kwargs)


class CategoryView(ListAPIView):
    """
    View for getting a list of categories
    """

    queryset = Category.objects.filter()
    serializer_class = CategorySerializer


class ProductsView(ListAPIView):
    """
    View for getting a list of products
    """
    queryset = ProductInfo.objects.filter()
    serializer_class = ProductInfoSerializer


class ProductInfoView(ListAPIView):
    """
    View for getting product's info
    """

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
    View for getting current user
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'current_user'

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class BasketView(APIView):
    """
    View for managing a user's basket (shopping cart)
    """

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
                            basket = Order.objects.create(user_id=request.user.id, status='basket')
                            new_order_created = True

                        order_item.update({'order': basket.id})

                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        serializer.save()
                        objects_created += 1
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': True, 'Objects created:': objects_created})
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Invalid JSON format'})
        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})

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
                    return JsonResponse({'Status': True, 'Objects deleted:': deleted_count})
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
                                                 'Errors': 'OrderItem not found for the user'
                                                           'or order_id and order_item_id do not match'})

                        serializer = OrderItemSerializer(instance=order_item, data=order_item_data)
                        if serializer.is_valid():
                            serializer.save()
                            objects_updated += 1
                        else:
                            return JsonResponse({'Status': False, 'Errors': serializer.errors})
                    else:
                        return JsonResponse({'Status': False,
                                             'Errors': 'Both order_item_id and order_id must be specified'
                                                       ' for an item in PUT request'})

                return JsonResponse({'Status': True, 'Objects updated: ': objects_updated})
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Invalid JSON format'})
        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})


class OrderView(APIView):
    """
    View for getting and updating orders
    """

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
            if request.data['id']:
                try:
                    order_id = request.data['id']
                    order_status = 'new'
                    new_order_task.delay(user_id=request.user.id, order_id=order_id, order_status=order_status)
                    return JsonResponse({'Status': True})
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Wrong arguments'})

        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})


class PartnerState(APIView):
    """
    View for getting and changing partner state
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Shops only'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Shops only'}, status=403)
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})


class PartnerOrders(APIView):
    """
    View for getting partner's orders
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Shops only'}, status=403)
        # print(request.user.id)
        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        # print(order.query)

        serializer = OrderSerializer(order, many=True)
        # print(serializer.data)
        return Response(serializer.data)


class ContactView(APIView):
    """
    View for getting and creating contacts
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        contacts = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        required_fields = {'city', 'street', 'phone'}
        if required_fields.issubset(request.data):
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_string = request.data.get('items')
        if items_string:
            items_list = items_string.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Objects deleted': deleted_count})

        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        contact_id = request.data.get('id')
        if contact_id and contact_id.isdigit():
            contact = Contact.objects.filter(id=contact_id, user_id=request.user.id).first()
            if contact:
                serializer = ContactSerializer(contact, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Required arguments are not specified'})


class TestEmailView(APIView):
    """
    View for testing celery
    """

    def get(self, request):
        send_test_email_task.delay(email_address='a.zhmetko@gmail.com', message='Test Test Test')
        return JsonResponse({'Status': True})


class CustomResetPasswordRequestToken(ResetPasswordRequestToken):
    """
    Reset password token request customization
    """

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        email = request.data.get('email')
        reset_password_token = ResetPasswordToken.objects.filter(user__email=email).first()

        if reset_password_token:
            password_reset_token_created_task.delay(email, reset_password_token)

        return response
