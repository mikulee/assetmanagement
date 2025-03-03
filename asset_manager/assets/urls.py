from django.urls import path
from django.views.generic.base import RedirectView
from .views import AssetListView, AssetCreateView, AssetUpdateView, AssetDeleteView

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/', permanent=True), name='root'),
    path('dashboard/', AssetListView.as_view(), name='dashboard'),
    path('asset/new/', AssetCreateView.as_view(), name='asset-create'),
    path('asset/<int:pk>/update/', AssetUpdateView.as_view(), name='asset-update'),
    path('asset/<int:pk>/delete/', AssetDeleteView.as_view(), name='asset-delete'),
]