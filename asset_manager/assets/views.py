from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Asset, Customer, UserRole
from .forms import AssetForm, CustomerForm, UserCreateForm, UserRoleForm

class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'assets/dashboard.html'
    context_object_name = 'assets'

    def get_queryset(self):
        queryset = Asset.objects.select_related('customer')
        
        if hasattr(self.request.user, 'userrole') and self.request.user.userrole.role == 'admin':
            pass
        elif hasattr(self.request.user, 'userrole'):
            queryset = queryset.filter(customer__in=self.request.user.userrole.customers.all())
        else:
            queryset = Asset.objects.none()

        # Get filter parameters
        search = self.request.GET.get('search', '')
        asset_type = self.request.GET.get('asset_type', '')
        criticality = self.request.GET.get('criticality', '')
        status = self.request.GET.get('status', '')
        customer = self.request.GET.get('customer', '')
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
        if customer and self.request.user.userrole.role in ['admin', 'manager']:
            queryset = queryset.filter(customer_id=customer)

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
        if hasattr(self.request.user, 'userrole') and self.request.user.userrole.role in ['admin', 'manager']:
            if self.request.user.userrole.role == 'admin':
                context['customers'] = Customer.objects.all()
            else:
                context['customers'] = self.request.user.userrole.customers.all()
            context['current_filters']['customer'] = self.request.GET.get('customer', '')
        return context

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('dashboard')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.userrole.role != 'admin':
            # Non-admin users can only see their assigned customers
            form.fields['customer'].queryset = self.request.user.userrole.customers.all()
        return form

    def form_valid(self, form):
        if not self.request.user.is_staff:
            # Ensure non-staff users can only create assets for their customer
            form.instance.customer = self.request.user.customer
        return super().form_valid(form)

class AssetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        asset = self.get_object()
        # Allow access if user is admin or asset's customer is in user's assigned customers
        return (self.request.user.userrole.role == 'admin' or 
                asset.customer in self.request.user.userrole.customers.all())

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.userrole.role != 'admin':
            # Non-admin users can only see their assigned customers
            form.fields['customer'].queryset = self.request.user.userrole.customers.all()
        return form

class AssetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Asset
    success_url = reverse_lazy('dashboard')
    template_name = 'assets/asset_confirm_delete.html'

    def test_func(self):
        asset = self.get_object()
        # Allow access if user is admin or asset's customer is in user's assigned customers
        return (self.request.user.userrole.role == 'admin' or 
                asset.customer in self.request.user.userrole.customers.all())

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
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'assets/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        # Show all customers to admin and manager
        if hasattr(self.request.user, 'userrole') and self.request.user.userrole.role in ['admin', 'manager']:
            return Customer.objects.all()
        # Show assigned customers to regular users
        elif hasattr(self.request.user, 'userrole'):
            return self.request.user.userrole.customers.all()
        return Customer.objects.none()

# Update CustomerCreateView
class CustomerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'assets/customer_form.html'
    success_url = reverse_lazy('customer-list')

    def test_func(self):
        return hasattr(self.request.user, 'userrole') and self.request.user.userrole.role in ['admin', 'manager']

# Update CustomerUpdateView
class CustomerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'assets/customer_form.html'
    success_url = reverse_lazy('customer-list')

    def test_func(self):
        return hasattr(self.request.user, 'userrole') and self.request.user.userrole.role in ['admin', 'manager']

    def get_queryset(self):
        if self.request.user.userrole.role == 'admin':
            return Customer.objects.all()
        return self.request.user.userrole.customers.all()

# Update CustomerDeleteView
class CustomerDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('customer-list')
    template_name = 'assets/customer_confirm_delete.html'

    def test_func(self):
        return hasattr(self.request.user, 'userrole') and self.request.user.userrole.role in ['admin', 'manager']

    def get_queryset(self):
        if self.request.user.userrole.role == 'admin':
            return Customer.objects.all()
        return self.request.user.userrole.customers.all()

# Add after existing views
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'assets/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return (hasattr(self.request.user, 'userrole') and 
                self.request.user.userrole.role in ['admin', 'manager'])

    def get_queryset(self):
        if self.request.user.userrole.role == 'admin':
            return User.objects.all()
        # Managers can only see users assigned to their customers
        return User.objects.filter(
            userrole__customers__in=self.request.user.userrole.customers.all()
        ).distinct()

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

    def get_object(self, queryset=None):
        user = User.objects.get(pk=self.kwargs['pk'])
        role, created = UserRole.objects.get_or_create(
            user=user,
            defaults={'role': 'user'}
        )
        return role

    def get_queryset(self):
        if self.request.user.userrole.role == 'admin':
            return UserRole.objects.all()
        return UserRole.objects.filter(
            customers__in=self.request.user.userrole.customers.all()
        ).distinct()
