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

from leffalippu.models import Order, Category, OrderedTickets

from captcha.fields import ReCaptchaField
#from captcha.fields import CaptchaField

# debugging
import inspect

import bitcoin

MAX_AMOUNT = 5

class OrderForm(forms.ModelForm):

    ## captcha = ReCaptchaField(attrs={'theme': 'clean',
    ##                                 'lang': 'fi'})

    terms = forms.BooleanField()
    
    class Meta:
        model = Order
        fields = ('email',)
        widgets = { 
        #'email': forms.TextInput(attrs={'placeholder': u'sähköposti'}),
        }   

    def clean(self):
        """
        Custom validation.

        1) The email address doesn't have other open orders
        """
        cleaned_data = super(OrderForm, self).clean()

        # TODO/FIXME: Check the email!
        
        return cleaned_data

class OrderedTicketsForm(forms.ModelForm):
    amount = forms.IntegerField(required=False,
                                initial=0,
                                min_value=0,
                                max_value=MAX_AMOUNT)

    class Meta:
        model = OrderedTickets
        fields = ('amount','category',)
        widgets = {'category': forms.HiddenInput}

    def clean(self):
        """
        Custom validation.

        1) Chect that the requested category is for sale

        2) The requested amount does not exceed the amount of available
        """

        # Validate the fields
        cleaned_data = super(OrderedTicketsForm, self).clean()
        if any(self.errors):
            return cleaned_data

        # Check that there are enough tickets available
        # TODO: You could put this validation into a custom field class.
        category = cleaned_data['category']
        if (cleaned_data['amount'] > 0 
            and cleaned_data['amount'] > category.amount_available()):
            
            raise forms.ValidationError("Lippuja ei ole riittävästi saatavilla.")

        return cleaned_data
                                
class BaseOrderedTicketsFormSet(BaseFormSet):

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

        # An order may contain each ticket category only once. This error is
        # prevented in UI, but some people may try to cheat the system by
        # sending custom POST messages.
        categories = []
        for form in self.forms:
            category = form.cleaned_data['category']
            if category in categories:
                raise forms.ValidationError("Tilaus voi sisältää kunkin lipputyypin "
                                            "korkeintaan kerran.")
            categories.append(category)

        return

    def save(self, order):
        """
        Custom save method for the form set.

        Save only non-zero ticket orders.

        Paranoid check: At the end, check that the amount of available
        tickets for any category is not negative, if several people
        made simultaneous orders. If a negative amount is found,
        delete all these just saved orders and return False.
        """
        for form in self.forms:
            amount = form.cleaned_data['amount']
            if amount > 0:
                # Save only non-zero ticket categories
                category = form.cleaned_data['category']
                reserved_tickets = OrderedTickets(order=order,
                                                   category=category,
                                                   amount=amount,
                                                   price=category.price)
                reserved_tickets.save()

                if category.amount_available() < 0:
                    # This error should not happen. However, if
                    # simultaneous purchases happen, it may be that
                    # they both reserve "the same" tickets and the
                    # amount of available tickets becomes
                    # negative. Thus, cancel this order.
                    errors = form._errors.setdefault(NON_FIELD_ERRORS, ErrorList())
                    errors.append("Lippuja ei ole riittävästi saatavilla.")
                    OrderedTickets.objects.filter(order=order).delete()
                    return False
                
        try:
            (address, price) = bitcoin.create_payment(order)
            order.bitcoin_address = address
            order.price_satoshi = price
            order.save()
            return True
        except Exception as e:
            print(e)
            # This error should happen only if the bitcoin payment could not be
            # created, for instance, if blockchain.info or mtgox.com is down.
            self._non_form_errors = ErrorList(["Maksua ei kyetty luomaan. "
                                               "Käytetyt Bitcoin-palvelut "
                                               "todennäköisesti tilapäisesti "
                                               "poissa käytöstä. Yritä "
                                               "myöhemmin uudelleen."])

            return False

        
