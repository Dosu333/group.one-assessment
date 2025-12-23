from django.db import models
import uuid


LICENSE_STATUS_CHOICES = (
    ('VALID', 'VALID'),
    ('SUSPENDED', 'SUSPENDED'),
    ('CANCELLED', 'CANCELLED')
)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Brand(BaseModel):
    name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True)
    webhook_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,
                              related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class LicenseKey(BaseModel):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,
                              related_name='license_keys')
    key_string = models.CharField(max_length=255, unique=True)
    customer_email = models.EmailField()

    def __str__(self):
        return self.key_string


class License(BaseModel):
    license_key = models.ForeignKey(LicenseKey, on_delete=models.CASCADE,
                                    related_name='licenses')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='licenses')
    status = models.CharField(max_length=20, choices=LICENSE_STATUS_CHOICES,
                              default='VALID')
    expiration_date = models.DateTimeField(blank=True, null=True)
    seat_limit = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.license_key.key_string} - {self.product.name}"


class Activation(BaseModel):
    license = models.ForeignKey(License, on_delete=models.CASCADE,
                                related_name='activations')
    instance_identifier = models.CharField(max_length=255)

    def __str__(self):
        return self.instance_identifier
