from django import forms
from leffaliput import models

class ReservationForm(forms.ModelForm):
    class Meta:
        model = models.Reservation
        fields = ('email',)

class ReservedTicketsForm(forms.ModelForm):
    amount = forms.IntegerField(required=False,
                                initial=0,
                                min_value=0,
                                max_value=6)
                                
    class Meta:
        model = models.ReservedTickets
        fields = ('amount','category',)
        widgets = {'category': forms.HiddenInput}
