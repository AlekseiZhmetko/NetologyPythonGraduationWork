from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator
from easy_thumbnails.fields import ThumbnailerImageField

USER_TYPE_CHOICES = (
    ('shop', 'Shop'),
    ('buyer', 'Buyer'),
)

ORDER_STATUSES = (
    ('basket', 'Basket'),
    ('new', 'New'),
    ('confirmed', 'Confirmed'),
    ('assembled', 'Ready for shipping'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('returned', 'Returned'),
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'username'
    email = models.EmailField(_('Email'), unique=True,
                              error_messages={'unique': _("This email address is already exists."),
                                              },
                              )
    company = models.CharField(verbose_name='Company', max_length=40, blank=True)
    position = models.CharField(verbose_name='Position', max_length=40, blank=True)
    first_name = models.CharField(verbose_name='First name', max_length=40, blank=True)
    middle_name = models.CharField(verbose_name='Middle name', max_length=40, blank=True)
    last_name = models.CharField(verbose_name='Last name', max_length=40, blank=True)
    username = models.CharField(
        _('Username'),
        max_length=150, unique=True,
        blank=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'))
    avatar = ThumbnailerImageField(
        _('Avatar'),
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_('Upload an image for the user avatar.'),
        resize_source=dict(size=(300, 300), crop='smart'))

    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Avatar')

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    type = models.CharField(verbose_name='User type', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = "User list"
        ordering = ('email',)


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='Name')
    url = models.URLField(null=True, blank=True, verbose_name='Url')
    user = models.OneToOneField(User, verbose_name='User',
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    state = models.BooleanField(verbose_name='Getting orders status', default=True)

    # filename = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Shop'
        verbose_name_plural = "Shops list"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='Name')
    shops = models.ManyToManyField(Shop, verbose_name='Shops', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories list'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Name')
    category = models.ForeignKey(Category, verbose_name='Category', related_name='products', blank=True,
                                 on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, verbose_name='Product', related_name='product_infos', blank=True,
                                on_delete=models.CASCADE)
    external_id = models.IntegerField(verbose_name='External ID', blank=True)
    model = models.CharField(max_length=80, verbose_name='Model', blank=True)
    shop = models.ForeignKey(Shop, verbose_name='Shop', related_name='product_infos', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.IntegerField(verbose_name='Quantity')
    price = models.IntegerField(verbose_name='Price')
    price_rrc = models.IntegerField(verbose_name='Recommended retail price')

    class Meta:
        verbose_name = 'Product info'
        verbose_name_plural = "Product info list"


class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='Name')

    class Meta:
        verbose_name = 'Parameter name'
        verbose_name_plural = "Parameter names list"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Product info',
                                     related_name='product_parameters', blank=True,
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Parameter', related_name='product_parameters', blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Value', max_length=100)

    class Meta:
        verbose_name = 'Parameter'
        verbose_name_plural = "Parameters list"


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='User',
                             related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    city = models.CharField(max_length=50, verbose_name='City', blank=True)
    street = models.CharField(max_length=100, verbose_name='Street', blank=True)
    building = models.CharField(max_length=15, verbose_name='Building', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Apartment', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Phone', blank=True)

    class Meta:
        verbose_name = 'User contacts'
        verbose_name_plural = 'User contacts list'

    def __str__(self):
        return self.user


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='User',
                             related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Status', choices=ORDER_STATUSES, max_length=20, blank=True)
    contact = models.ForeignKey(Contact, verbose_name='Contact',
                                blank=True, null=True,
                                on_delete=models.CASCADE)

    def total_sum(self):
        total_sum = sum(item.product_info.price * item.quantity for item in self.ordered_items.all())
        return total_sum

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = "Orders list"
        ordering = ('-dt',)

    def __str__(self):
        return str(self.dt)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Order', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)

    product_info = models.ForeignKey(ProductInfo, verbose_name='Product info', related_name='ordered_items',
                                     blank=True,
                                     on_delete=models.CASCADE)
    quantity = models.IntegerField(verbose_name='Quantity')

    class Meta:
        verbose_name = 'Ordered item'
        verbose_name_plural = "Ordered items list"


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("The User which is associated to this password reset token")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("When was this token generated")
    )

    key = models.CharField(
        _("Key"),
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)
