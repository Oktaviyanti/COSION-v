from django import forms

class FormUpload(forms.Form):
    images = forms.ImageField()