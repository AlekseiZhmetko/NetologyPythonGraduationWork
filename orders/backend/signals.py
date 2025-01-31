import json

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
import os
from django.contrib.auth.models import User
from .serializers import OrderSerializer
from .models import ConfirmEmailToken, User, Order, Shop
from dotenv import load_dotenv


load_dotenv()
new_user_registered = Signal('user_id')

new_order = Signal('user_id')


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Signal with password reset token
    """
    # send an e-mail to the user

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {reset_password_token.user}",
        # message:
        reset_password_token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )
    msg.send()


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    """
    Signal for new user
    """

    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    user = User.objects.get(id=user_id)

    body = f"Here's data about you:\n\n" \
           f"User ID: {user.id}\n" \
           f"Username: {user.username}\n"\
           f"Email: {user.email}\n" \
           f"Company: {user.company}\n" \
           f"Position: {user.position}\n" \
           f"Name: {user.first_name} {user.last_name}\n" \

    msg = EmailMultiAlternatives(
        subject=f"Thank you for the registration {user.email}",
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )
    if token.user.email == 'test@test.com':
        with open(os.getenv('path_file'), 'w') as s:
            json.dump({'tok': token.key}, s)
    msg.send()


@receiver(new_order)
def new_order_signal(user_id, order_id, order_status, **kwargs):
    """
    Signal with new order's data (sending to buyer and Shop admin)
    """
    user = User.objects.get(id=user_id)
    order = Order.objects.get(id=order_id)

    order_serializer = OrderSerializer(order)
    order_data = order_serializer.data
    pretty_order_data = json.dumps(order_data, indent=4, ensure_ascii=False)

    subject_buyer = f"Order #{order_id} Status Update"
    message_buyer = f"Order #{order_id} has been updated.\n Details:\n\n{pretty_order_data}" \
                    f"\n\nCurrent Status: {order_status}\n\n"

    msg_buyer = EmailMultiAlternatives(
        subject=subject_buyer,
        body=message_buyer,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )
    msg_buyer.send()

    try:
        shop_admin_user_id = order.ordered_items.first().product_info.shop.user_id
        shop_admin = User.objects.get(id=shop_admin_user_id)

        subject_admin = f"New Order #{order_id} Received"
        message_admin = f"A new order #{order_id} has been received for your shop." \
                        f"\n\nOrder Details:\n\n{pretty_order_data}\n\nCurrent Status: {order_status}\n\n"

        msg_admin = EmailMultiAlternatives(
            subject=subject_admin,
            body=message_admin,
            from_email=settings.EMAIL_HOST_USER,
            to=[shop_admin.email]
        )
        msg_admin.send()

    except AttributeError:
        pass
