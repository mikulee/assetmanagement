from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import Asset, UserProfile, Customer  # Add Customer to imports
from .forms import AssetForm  # Add this import
from django.db.models import Q
from django.contrib import messages

class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'assets/dashboard.html'
    context_object_name = 'assets'

    def get_queryset(self):
        queryset = Asset.objects.filter(customer=self.request.user.customer)
        
        # Get filter parameters from GET request
        search = self.request.GET.get('search', '')
        asset_type = self.request.GET.get('asset_type', '')
        criticality = self.request.GET.get('criticality', '')
        status = self.request.GET.get('status', '')
        sort = self.request.GET.get('sort', '-last_checked')

        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(ip_address__icontains=search)
            )
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)
        if criticality:
            queryset = queryset.filter(business_criticality=criticality)
        if status:
            queryset = queryset.filter(status=status == 'active')

        # Apply sorting
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asset_types'] = Asset.ASSET_TYPES
        context['criticality_choices'] = Asset.CRITICALITY_CHOICES
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'asset_type': self.request.GET.get('asset_type', ''),
            'criticality': self.request.GET.get('criticality', ''),
            'status': self.request.GET.get('status', ''),
            'sort': self.request.GET.get('sort', '-last_checked')
        }
        return context

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm  # Change this line
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        form.instance.customer = self.request.user.customer
        return super().form_valid(form)

class AssetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Asset
    form_class = AssetForm  # Change this line
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        asset = self.get_object()
        return self.request.user.customer == asset.customer

class AssetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Asset
    success_url = reverse_lazy('dashboard')
    template_name = 'assets/asset_confirm_delete.html'

    def test_func(self):
        asset = self.get_object()
        return self.request.user.customer == asset.customer

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Asset successfully deleted.')
        return super().delete(request, *args, **kwargs)

def dashboard(request):
    # Ensure user profile exists
    UserProfile.objects.get_or_create(user=request.user)
    
    # Rest of your dashboard view code
    context = {
        'user_profile': request.user.userprofile,
        # ... other context data ...
    }
    return render(request, 'assets/dashboard.html', context)

# Create your views here.
