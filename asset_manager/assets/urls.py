from django.urls import path
from django.views.generic.base import RedirectView
from .views import (
    AssetListView, AssetCreateView, AssetUpdateView, AssetDeleteView,
    CustomerListView, CustomerCreateView, CustomerUpdateView, CustomerDeleteView,
    UserListView, UserCreateView, UserUpdateView, UserRoleUpdateView  # Add these
)

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/', permanent=True), name='root'),
    path('dashboard/', AssetListView.as_view(), name='dashboard'),
    
    # Asset URLs
    path('asset/new/', AssetCreateView.as_view(), name='asset-create'),
    path('asset/<int:pk>/update/', AssetUpdateView.as_view(), name='asset-update'),
    path('asset/<int:pk>/delete/', AssetDeleteView.as_view(), name='asset-delete'),
    
    # Customer URLs
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customer/new/', CustomerCreateView.as_view(), name='customer-create'),
    path('customer/<int:pk>/update/', CustomerUpdateView.as_view(), name='customer-update'),
    path('customer/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer-delete'),
    
    # User management URLs
    path('users/', UserListView.as_view(), name='user-list'),
    path('user/new/', UserCreateView.as_view(), name='user-create'),
    path('user/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('user/<int:pk>/role/', UserRoleUpdateView.as_view(), name='user-role'),
]