from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import Asset, UserProfile, Customer, UserRole
from .forms import AssetForm, CustomerForm, UserCreateForm, UserRoleForm
from django.db.models import Q
from django.contrib import messages

class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'assets/dashboard.html'
    context_object_name = 'assets'

    def get_queryset(self):
        queryset = Asset.objects.select_related('customer')  # Add this line for efficient querying
        if not self.request.user.is_staff:
            queryset = queryset.filter(customer=self.request.user.customer)
        
        # Get filter parameters from GET request
        search = self.request.GET.get('search', '')
        asset_type = self.request.GET.get('asset_type', '')
        criticality = self.request.GET.get('criticality', '')
        status = self.request.GET.get('status', '')
        customer = self.request.GET.get('customer', '')  # Add this line
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
        if customer and self.request.user.is_staff:  # Add this block
            queryset = queryset.filter(customer_id=customer)

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
        if self.request.user.is_staff:
            context['customers'] = Customer.objects.all()
        context['current_filters']['customer'] = self.request.GET.get('customer', '')
        return context

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('dashboard')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_staff:
            # Non-staff users can only see their own customer
            form.fields['customer'].queryset = Customer.objects.filter(user=self.request.user)
            form.fields['customer'].initial = self.request.user.customer
            form.fields['customer'].widget.attrs['disabled'] = 'disabled'
        return form

    def form_valid(self, form):
        if not self.request.user.is_staff:
            # Ensure non-staff users can only create assets for their customer
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

# Add these new view classes:
class CustomerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Customer
    template_name = 'assets/customer_list.html'
    context_object_name = 'customers'

    def test_func(self):
        return self.request.user.is_staff

class CustomerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'assets/customer_form.html'
    success_url = reverse_lazy('customer-list')

    def test_func(self):
        return self.request.user.is_staff

class CustomerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'assets/customer_form.html'
    success_url = reverse_lazy('customer-list')

    def test_func(self):
        return self.request.user.is_staff

class CustomerDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('customer-list')
    template_name = 'assets/customer_confirm_delete.html'

    def test_func(self):
        return self.request.user.is_staff

# Add after existing views
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'assets/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return hasattr(self.request.user, 'userrole') and self.request.user.userrole.role in ['admin', 'manager']

    def get_queryset(self):
        if self.request.user.userrole.role == 'admin':
            return User.objects.all()
        return User.objects.filter(userrole__customers__in=self.request.user.userrole.customers.all()).distinct()

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'assets/user_form.html'
    success_url = reverse_lazy('user-list')

    def test_func(self):
        return self.request.user.userrole.role in ['admin', 'manager']

    def form_valid(self, form):
        response = super().form_valid(form)
        UserRole.objects.create(user=self.object, role='user')
        return response

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    template_name = 'assets/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name']
    success_url = reverse_lazy('user-list')

    def test_func(self):
        return self.request.user.userrole.role in ['admin', 'manager']

class UserRoleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserRole
    form_class = UserRoleForm
    template_name = 'assets/user_role_form.html'
    success_url = reverse_lazy('user-list')

    def test_func(self):
        return self.request.user.userrole.role in ['admin', 'manager']

    def get_queryset(self):
        if self.request.user.userrole.role == 'admin':
            return UserRole.objects.all()
        return UserRole.objects.filter(
            customers__in=self.request.user.userrole.customers.all()
        ).distinct()
