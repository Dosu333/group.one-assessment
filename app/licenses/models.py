from django.db import models
from django.utils.text import slugify
import secrets
import uuid


LICENSE_STATUS_CHOICES = (
    ('valid', 'Valid'),
    ('suspended', 'Suspended'),
    ('cancelled', 'Cancelled'),
)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Brand(BaseModel):
    name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True, editable=False)
    slug = models.SlugField(unique=True)

    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        while Brand.objects.filter(slug=slug).exclude(id=self.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()

        if not self.api_key:
            self.api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(BaseModel):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,
                              related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def generate_unique_slug(self):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        while Product.objects.filter(slug=slug).exclude(id=self.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

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
                              default='valid')
    expiration_date = models.DateTimeField(blank=True, null=True)
    seat_limit = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.license_key.key_string} - {self.product.name}"


class Activation(BaseModel):
    license = models.ForeignKey(License, on_delete=models.CASCADE,
                                related_name='activations')
    instance_identifier = models.CharField(max_length=255)

    class Meta:
        unique_together = ('license', 'instance_identifier')

    def __str__(self):
        return self.instance_identifier


class IdempotencyRecord(BaseModel):
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    idempotency_key = models.CharField(max_length=255)
    response_data = models.JSONField()
    status_code = models.IntegerField()

    class Meta:
        unique_together = ('brand', 'idempotency_key')
        indexes = [
            models.Index(fields=['brand', 'idempotency_key']),
        ]
