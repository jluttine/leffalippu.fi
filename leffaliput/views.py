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

"""
Views for `leffaliput`.
"""



from django.shortcuts import render
from django.db.models import Count, Sum
from django.forms.models import modelformset_factory, inlineformset_factory
from django.forms.formsets import formset_factory

from django.views.generic import View, TemplateView

from leffaliput.models import *
from leffaliput import forms

def order(request):

    if request.method == 'POST':

        # Form set for providing quantities for each ticket category
        CategoryFormSet = formset_factory(forms.ReservedTicketsForm)

        # Read user input
        reservation_form = forms.ReservationForm(request.POST)
        category_formset = CategoryFormSet(request.POST)

        # Validate the input
        valid_tickets = category_formset.is_valid()
        valid_reservation = reservation_form.is_valid()
        if valid_tickets and valid_reservation:
            # do processing, saving,...
            print("IN POST SUCCESS!")
            
            return render(request,
                          'leffaliput/order.html',
                          {
                          })

    # Open reservations
    reservation_list = Reservation.objects.filter(transaction=None)

    # All transactions
    transaction_list = Transaction.objects.all()

    # All tickets
    ticket_list = Ticket.objects.all()

    # The ticket categories that are for sale
    category_list = Category.objects.all()
    num_categories = len(category_list)

    # Amount of reserved/buyed tickets
    category_list = category_list.annotate(amount_reserved=Sum('reservedtickets__amount'))
    # Total amount of tickets
    category_list = category_list.annotate(amount_total=Count('ticket'))
    # Compute the number of available tickets
    for category in category_list:
        if category.amount_reserved:
            category.amount_available = category.amount_total - category.amount_reserved
        else:
            category.amount_available = category.amount_total

    if request.method != 'POST':
        reservation_form = forms.ReservationForm()
        
        CategoryFormSet = formset_factory(forms.ReservedTicketsForm, 
                                          extra=num_categories)
        category_formset = CategoryFormSet()
        for (form, category) in zip(category_formset, category_list):
            form.fields['category'].initial = category

    
    return render(request, 
                  'leffaliput/home.html',
                  {
                      'ticket_list':      ticket_list,
                      'category_list':    category_list,
                      'reservation_list': reservation_list,
                      'transaction_list': transaction_list,
                      'reservation_form': reservation_form,
                      'category_formset': category_formset,
                  })
