from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Contact, ContactCategory
from .forms import ContactForm

# Create your views here.

def contact_form(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.created_by = request.user if request.user.is_authenticated else None
            contact.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact:contact_form')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'contact/contact_form.html', {'form': form})
