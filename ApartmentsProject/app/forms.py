from django import forms


class ObjectForm(forms.Form):
    address = forms.CharField(required=True)
    rooms = forms.CharField(required=True)
    level = forms.CharField(required=True)
    levels = forms.CharField(required=True)
    area = forms.CharField(required=True)
    kitchen_area = forms.CharField(required=True)
    postal_code = forms.CharField(required=True)