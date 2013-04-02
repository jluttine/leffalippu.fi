# -*- encoding: utf-8 -*- 

# Copyright (C) 2013 Jaakko Luttinen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

from django import forms
from django.forms.formsets import BaseFormSet

from django.forms.util import ErrorList
from django.forms.forms import NON_FIELD_ERRORS

from leffaliput.models import Reservation, Category, ReservedTickets

# debugging
import inspect

MAX_AMOUNT = 5

class ReservationForm(forms.ModelForm):
    
    class Meta:
        model = Reservation
        fields = ('email',)

    def clean(self):
        """
        Custom validation.

        1) The email address doesn't have other open orders
        """
        cleaned_data = super(ReservationForm, self).clean()
        return cleaned_data

class ReservedTicketsForm(forms.ModelForm):
    amount = forms.IntegerField(required=False,
                                initial=0,
                                min_value=0,
                                max_value=MAX_AMOUNT)

    class Meta:
        model = ReservedTickets
        fields = ('amount','category',)
        widgets = {'category': forms.HiddenInput}

    def clean(self):
        """
        Custom validation.

        1) Chect that the requested category is for sale

        2) The requested amount does not exceed the amount of available
        """

        # Validate the fields
        cleaned_data = super(ReservedTicketsForm, self).clean()
        if any(self.errors):
            return cleaned_data

        # Check that there are enough tickets available
        # TODO: You could put this validation into a custom field class.
        category = cleaned_data['category']
        if (cleaned_data['amount'] > 0 
            and cleaned_data['amount'] > category.amount_available()):
            
            raise forms.ValidationError("Lippuja ei ole riittävästi saatavilla.")

        return cleaned_data
                                
class BaseReservedTicketsFormSet(BaseFormSet):

    def clean(self):
        """
        Custom validation.

        1) The total amount of tickets does not exceed the limit

        2) The total amount of tickets is greater than zero.
        
        3) The same category is not requested several times (if they
        attempt to order too many tickets by sending several small
        amounts of the same category in one order using custom POST
        requests).
        """

        # Don't validate the formset unless each form is valid on its own
        if any(self.errors):
            return

        # Check that the total amount of tickets is in range [1, MAX_AMOUNT]
        total_amount = 0
        for form in self.forms:
            total_amount += form.cleaned_data['amount']

        if total_amount > MAX_AMOUNT:
            raise forms.ValidationError("Voit tilata yhteensä korkeintaan %s lippua." % MAX_AMOUNT)
        if total_amount <= 0:
            raise forms.ValidationError("Tilauksen täytyy sisältää vähintään yksi lippu.")

        # An order may contain each ticket category only once. This
        # error is prevented in UI, but some people may try to send
        # cheat the system by sending custom POST messages.
        categories = []
        for form in self.forms:
            category = form.cleaned_data['category']
            if category in categories:
                raise forms.ValidationError("Tilaus voi sisältää kunkin lipputyypin "
                                            "korkeintaan kerran.")
            categories.append(category)

        return

    def save(self, reservation):
        """
        Custom save method for the form set.

        Save only non-zero ticket orders.

        Paranoid check: At the end, check that the amount of available
        tickets for any category is not negative, if several people
        made simultaneous orders. If a negative amount is found,
        delete all these just saved reservations and return False.
        """
        for form in self.forms:
            amount = form.cleaned_data['amount']
            if amount > 0:
                # Save only non-zero ticket categories
                category = form.cleaned_data['category']
                reserved_tickets = ReservedTickets(reservation=reservation,
                                                   category=category,
                                                   amount=amount,
                                                   price=category.price)
                reserved_tickets.save()

                if category.amount_available() < 0:
                    # This error should not happen. However, if
                    # simultaneous purchases happen, it may be that
                    # they both reserve "the same" tickets and the
                    # amount of available tickets becomes
                    # negative. Thus, cancel this reservation.
                    errors = form._errors.setdefault(NON_FIELD_ERRORS, ErrorList())
                    errors.append("Lippuja ei ole riittävästi saatavilla.")
                    ReservedTickets.objects.filter(reservation=reservation).delete()
                    return False
                
        return True

        
