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


from django.http import Http404
from django.shortcuts import render
from django.db.models import Count, Sum
from django.forms.models import modelformset_factory, inlineformset_factory
from django.forms.formsets import formset_factory

from django.views.generic import View, TemplateView

from leffaliput.models import *
from leffaliput import forms


import string
import random
def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

#def cancel(request):
def cancel(request, order_id):
    try:
        reservation = Reservation.objects.get(pk=order_id)
    except Reservation.DoesNotExist:
        raise Http404

    # Only open reservations can be cancelled
    if reservation.status == Reservation.OPEN:
        reservation.status = Reservation.CANCELLED
        reservation.save()
    
    return render(request,
                  'leffaliput/cancel.html',
                  {
                      'reservation': reservation,
                      'CANCELLED': reservation.CANCELLED,
                      'PAID': reservation.PAID,
                      'EXPIRED': reservation.EXPIRED,
                  })
        

def pay(request, order_id):
    """
    Complete the reservation by adding tickets to it and marking it paid.
    """
    try:
        reservation = Reservation.objects.get(pk=order_id)
    except Reservation.DoesNotExist:
        raise Http404

    # Only open reservations can be paid
    if reservation.status == Reservation.OPEN:

        # Mark the reservation paid
        reservation.status = Reservation.PAID
        reservation.save()
    
        # Create transaction
        transaction = Transaction(reservation=reservation)
        transaction.save()

        # Add tickets to it
        for reserved_tickets in ReservedTickets.objects.filter(reservation=reservation):
            category = reserved_tickets.category
            amount = reserved_tickets.amount
            tickets = Ticket.objects.filter(category=category,paidticket=None).order_by('expires')
            if len(tickets) < amount:
                # This should not happen: A customer has paid for more
                # tickets than we have available. If this ever
                # happens, it means there's a bug in this system.
                raise Exception("Serious bug in the system. Not enough tickets available.")
            amount_given = 0
            for ticket in tickets[:amount]:
                if amount_given == amount:
                    break
                paid_ticket = PaidTicket(ticket=ticket, transaction=transaction)
                try:
                    paid_ticket.save()
                    amount_given += 1
                except:
                    # This may happen extremely rarely: Someone has
                    # bought a ticket that was available when we
                    # filtered. This may happen if several customers
                    # are paying at the same time. However, there
                    # should be enough tickets available, so no need
                    # to worry.
                    pass
            if PaidTicket.objects.filter(transaction=transaction).count() != amount:
                # This should not happen: The system was not able to
                # provide enough tickets for the customer.
                raise Exception("Serious bug in the system. Not enough tickets given to the customer.")

    return render(request,
                  'leffaliput/pay.html',
                  {
                      'reservation': reservation,
                      'CANCELLED': reservation.CANCELLED,
                      'PAID': reservation.PAID,
                      'EXPIRED': reservation.EXPIRED,
                  })

def order(request):

    if request.method == 'POST':

        # Form set for providing quantities for each ticket category
        CategoryFormSet = formset_factory(forms.ReservedTicketsForm,
                                          formset=forms.BaseReservedTicketsFormSet)

        # Read user input
        reservation_form = forms.ReservationForm(request.POST)
        category_formset = CategoryFormSet(request.POST)

        # Validate the input
        valid_tickets = category_formset.is_valid()
        valid_reservation = reservation_form.is_valid()

        # Set field max values
        for form in category_formset:
            try:
                form.fields['amount'].available = form.instance.category.amount_available()
                max_value = min(form.fields['amount'].available, 
                                form.fields['amount'].max_value)
                max_value = max(0, max_value)
                form.fields['amount'].max_value = max_value
            except:
                pass

        if valid_tickets and valid_reservation:
            # Create the reservation
            reservation = reservation_form.save(commit=False)
            # Fill-in the missing fields
            reservation.status = 'O'
            reservation.private_key = id_generator()
            reservation.public_address = id_generator()
            reservation.ip = '192.128.1.1'
            reservation.save()
            if category_formset.save(reservation):
                return render(request,
                              'leffaliput/order.html',
                              {
                                  'reservation': reservation,
                              })
            reservation.delete()

    # Open reservations
    open_reservation_list = Reservation.objects.filter(status=Reservation.OPEN)

    # Cancelled reservations
    cancelled_reservation_list = Reservation.objects.filter(status=Reservation.CANCELLED)

    # Expired reservations
    expired_reservation_list = Reservation.objects.filter(status=Reservation.EXPIRED)

    # All transactions
    transaction_list = Transaction.objects.all()
    #transaction_list = Transaction.objects.annotate(price=Sum('reservation.reservedtickets_set.

    # All tickets
    ticket_list = Ticket.objects.all()

    if request.method != 'POST':
        reservation_form = forms.ReservationForm()
        
        # The ticket categories that are for sale
        category_list = Category.objects.filter(name__contains='BioRex')
        num_categories = len(category_list)
        CategoryFormSet = formset_factory(forms.ReservedTicketsForm, 
                                          extra=num_categories)
        category_formset = CategoryFormSet()
        for (form, category) in zip(category_formset, category_list):
            form.fields['category'].initial = category
            form.fields['amount'].available = category.amount_available()
            max_value = min(form.fields['amount'].available, 
                            form.fields['amount'].max_value)
            max_value = max(0, max_value)
            form.fields['amount'].max_value = max_value
    
    
    return render(request, 
                  'leffaliput/home.html',
                  {
                      'ticket_list':      ticket_list,
                      'open_reservation_list': open_reservation_list,
                      'cancelled_reservation_list': cancelled_reservation_list,
                      'expired_reservation_list': expired_reservation_list,
                      'transaction_list': transaction_list,
                      'reservation_form': reservation_form,
                      'category_formset': category_formset,
                  })
