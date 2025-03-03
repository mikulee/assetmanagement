from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Asset, Customer, UserRole
import json

class AssetForm(forms.ModelForm):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label=None  # Removes empty choice
    )
    
    configuration = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter settings as key=value pairs\nExample:\nservertype=DC, location=HQ, backup=daily'
        }),
        required=False,
        help_text='Enter settings as key=value pairs, separated by commas (,) or semicolons (;)'
    )
    
    patch_cycle = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        initial=30,
        min_value=1,
        help_text='Custom patch cycle in days, or choose from common values below'
    )
    
    patch_cycle_preset = forms.ChoiceField(
        choices=[('', 'Custom')] + Asset.PATCH_CYCLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'document.getElementById("id_patch_cycle").value = this.value;'
        })
    )

    class Meta:
        model = Asset
        fields = [
            'customer',  # Add customer to the beginning of fields list
            'name', 
            'asset_type', 
            'ip_address', 
            'status',
            'business_criticality',
            'patch_cycle',
            'configuration'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_type': forms.Select(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'business_criticality': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an edit form and we have existing configuration
        if self.instance.pk and self.instance.configuration:
            # Convert JSON to key=value format for display
            try:
                config_pairs = []
                for key, value in self.instance.configuration.items():
                    config_pairs.append(f"{key}={value}")
                self.initial['configuration'] = ', '.join(config_pairs)
            except Exception:
                # If conversion fails, show raw JSON
                self.initial['configuration'] = json.dumps(self.instance.configuration)

    def clean_configuration(self):
        config_text = self.cleaned_data.get('configuration', '').strip()
        if not config_text:
            return {}

        # First try to parse as JSON (for edit mode)
        try:
            json_config = json.loads(config_text)
            if isinstance(json_config, dict):
                return json_config
        except json.JSONDecodeError:
            # Not JSON, try key=value format
            try:
                pairs = [p.strip() for p in config_text.replace(';', ',').split(',')]
                config_dict = {}

                for pair in pairs:
                    if not pair.strip():
                        continue
                        
                    if '=' not in pair:
                        raise forms.ValidationError(f"Invalid format: '{pair}'. Use key=value format.")
                    
                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if not key:
                        raise forms.ValidationError("Empty keys are not allowed")
                    
                    config_dict[key] = value

                return config_dict

            except forms.ValidationError:
                raise
            except Exception as e:
                raise forms.ValidationError(f"Error processing configuration: {str(e)}")

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['display_name', 'legal_name', 'contact_person']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ['role', 'customers']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'customers': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }