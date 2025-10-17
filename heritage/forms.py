from django import forms
from django.utils import timezone
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["nome", "email", "data", "numero_persone", "note"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def clean_data(self):
        d = self.cleaned_data["data"]
        if d < timezone.localdate():
            raise forms.ValidationError("La data deve essere nel futuro.")
        return d
