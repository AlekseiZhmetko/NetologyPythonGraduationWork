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
    Signal for email confirmation
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    if token.user.email == 'test@test.com':
        with open(os.getenv('path_file'), 'w') as s:
            json.dump({'tok': token.key}, s)
    msg.send()


@receiver(new_order)
def new_order_signal(user_id, order_id, order_status, **kwargs):
    """
    Signal with new order's data (sending to buyer)
    """
    user = User.objects.get(id=user_id)
    order = Order.objects.get(id=order_id)

    order_serializer = OrderSerializer(order)

    order_data = order_serializer.data
    pretty_order_data = json.dumps(order_data, indent=4, ensure_ascii=False)

    subject = f"Order #{order_id} Status Update"
    message = f"{user.username},\n\nOrder #{order_id} has been updated.\n Details:\n\n{pretty_order_data}" \
              f"\n\nCurrent Status: {order_status}\n\n"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )

    msg.send()

