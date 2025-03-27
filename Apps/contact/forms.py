from django import forms
from .models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'email', 'phone', 'company', 'message', 'category']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        } 