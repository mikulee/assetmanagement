from django.db import models
from django.contrib.auth.models import User, AbstractUser, Group, Permission
from django.core.validators import validate_ipv46_address
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, default="Customer A")
    legal_name = models.CharField(max_length=200, default="A real big company")
    contact_person = models.CharField(max_length=100, default="Mike Cunt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']

class Asset(models.Model):
    ASSET_TYPES = (
        ('server', 'Server'),
        ('network', 'Network Device'),
        ('storage', 'Storage System'),
    )
    
    CRITICALITY_CHOICES = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
        ('test', 'Test'),
    )

    PATCH_CYCLE_CHOICES = [
        (14, '14 days'),
        (30, '30 days'),
        (60, '60 days'),
        (90, '90 days'),
        (180, '180 days'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES)
    ip_address = models.GenericIPAddressField()
    monitoring_status = models.BooleanField(default=True)
    last_checked = models.DateTimeField(auto_now=True)
    configuration = models.JSONField(default=dict)  # For log analysis settings
    status = models.BooleanField(default=True, verbose_name='Active')
    business_criticality = models.CharField(
        max_length=20,
        choices=CRITICALITY_CHOICES,
        default='normal',
        verbose_name='Business Criticality'
    )
    patch_cycle = models.PositiveIntegerField(
        default=30,
        verbose_name='Patch Cycle (days)'
    )

    class Meta:
        ordering = ['-last_checked']
        unique_together = ['customer', 'name']
    
    def clean(self):
        validate_ipv46_address(self.ip_address)
    
    def get_absolute_url(self):
        return reverse('asset-detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return f"{self.name} ({self.get_asset_type_display()})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add any additional fields you want for the user profile
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('user', 'User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    customers = models.ManyToManyField(Customer, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        permissions = [
            ("can_manage_users", "Can manage users"),  # Admin only
            ("can_view_users", "Can view users list"),  # Admin and Manager
            ("can_assign_customers", "Can assign customers to users"),  # Admin only
            ("can_view_all_customers", "Can view all customers"),  # Admin and Manager
        ]

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    from .models import UserProfile
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        Customer.objects.create(
            user=instance,
            display_name=f"Customer {instance.username}",  # Changed from 'name'
            legal_name=f"Company {instance.username}",
            contact_person=instance.get_full_name() or instance.username
        )

@receiver(post_save, sender=User)
def save_customer(sender, instance, **kwargs):
    try:
        if not instance.is_staff and hasattr(instance, 'customer'):
            instance.customer.save()
    except Customer.DoesNotExist:
        if not instance.is_staff:
            Customer.objects.create(
                user=instance,
                display_name=f"Customer {instance.username}",
                legal_name=f"Company {instance.username}",
                contact_person=instance.get_full_name() or instance.username
            )

@receiver(post_save, sender=User)
def create_user_role(sender, instance, created, **kwargs):
    if created:
        UserRole.objects.create(
            user=instance,
            role='user'
        )

@receiver(post_save, sender=User)
def save_user_role(sender, instance, **kwargs):
    try:
        instance.userrole.save()
    except UserRole.DoesNotExist:
        UserRole.objects.create(user=instance, role='user')

# Create your models here.
