from django import forms

class UploadImageForm(forms.Form):
    image = forms.ImageField()

from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
