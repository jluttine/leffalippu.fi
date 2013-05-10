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

"""
Views for `leffalippu`.
"""


from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.db.models import Count, Sum
from django.forms.models import modelformset_factory, inlineformset_factory
from django.forms.formsets import formset_factory
#from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

#from django.core import mail
from mail_templated import send_mail

from django.conf import settings

from django.views.generic import View, TemplateView

from leffalippu.models import *
from leffalippu import forms

import string
import random

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

    
#def cancel(request):
def cancel(request, order_id):
    try:
        order = Order.objects.get(encrypted_pk=order_id)
    except Order.DoesNotExist:
        raise Http404

    # Only open orders can be cancelled, so check that orderstatus does not
    # exist.
    try:
        order.status = order.orderstatus.status
    except OrderStatus.DoesNotExist:
        orderstatus = OrderStatus(order=order,
                                  status=OrderStatus.CANCELLED)
        try:
            orderstatus.save()
            order.status = orderstatus.status
        except:
            raise Exception("Order could not be cancelled. Handle this situation.")

        send_mail('email/cancel.txt',
                  {
                      'order': order,
                      'EMAIL_ADDRESS': settings.EMAIL_ADDRESS,
                  },
                  settings.EMAIL_ADDRESS,
                  [order.email])
        
    return render(request,
                  'leffalippu/cancel.html',
                  {
                      'order': order,
                      'CANCELLED': OrderStatus.CANCELLED,
                      'PAID': OrderStatus.PAID,
                      'EXPIRED': OrderStatus.EXPIRED,
                  })
        


## @login_required
## def pay(request, order_id):
##     """
##     Complete the order by adding tickets to it and marking it paid.

##     This is for debugging purposes only. In production, do not let users access
##     this view.
##     """
##     # TODO/FIXME: Check permissions!
##     try:
##         order = Order.objects.get(encrypted_pk=order_id)
##         pay_order(order)
##         return HttpResponseRedirect(reverse('admin:manager'))
##     except Order.DoesNotExist:
##         raise Http404

    ## return render(request,
    ##               'leffalippu/pay.html',
    ##               {
    ##                   'order': order,
    ##                   'CANCELLED': OrderStatus.CANCELLED,
    ##                   'PAID': OrderStatus.PAID,
    ##                   'EXPIRED': OrderStatus.EXPIRED,
    ##               })

    
## @login_required
## def delete(request, order_id):
##     # TODO/FIXME: Check permissions!
##     try:
##         order = Order.objects.get(encrypted_pk=order_id)
##         # Delete ticket payments for this order
##         #PaidTicket.objects.filter(orderstatus__order=order).delete()
##         # Delete the order
##         order.delete()
##         return HttpResponseRedirect(reverse('admin:manager'))
##     #return HttpResponseRedirect(reverse('manager', args=(request, order_id,)))
##     except Order.DoesNotExist:
##         raise Http404

def order(request):

    if request.method == 'POST':

        # Form set for providing quantities for each ticket category
        CategoryFormSet = formset_factory(forms.OrderedTicketsForm,
                                          formset=forms.BaseOrderedTicketsFormSet)

        # Read user input
        order_form = forms.OrderForm(request.POST)
        category_formset = CategoryFormSet(request.POST)

        # Validate the input
        valid_tickets = category_formset.is_valid()
        valid_order = order_form.is_valid()

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

        if valid_tickets and valid_order:
            # Create the order
            order = order_form.save(commit=False)
            # Fill-in the missing fields
            order.ip = get_client_ip(request)
            # Use temporary values for BTC address and price. They are
            # overwritten by proper values when saving the formset.
            order.public_address = ''.join(random.choice(string.ascii_uppercase+string.digits) 
                                           for x in range(12))
            order.price_satoshi = 0
            order.save()
            if category_formset.save(order):
                # Order succesfull. Send email and show summary
                CANCEL_URL = reverse('cancel', args=[order.encrypted_pk])
                CANCEL_URL = request.build_absolute_uri(CANCEL_URL)
                send_mail('email/order.txt',
                          {
                              'order': order,
                              'CANCEL_URL': CANCEL_URL,
                              'EMAIL_ADDRESS': settings.EMAIL_ADDRESS,
                          },
                          settings.EMAIL_ADDRESS,
                          [order.email])
                return render(request,
                              'leffalippu/order.html',
                              {
                                  'order': order,
                              })
            order.delete()

    if request.method != 'POST':
        order_form = forms.OrderForm()
        
        # The ticket categories that are for sale
        #category_list = Category.objects.filter(name__contains='BioRex')
        category_list = Category.objects.all()
        num_categories = len(category_list)
        CategoryFormSet = formset_factory(forms.OrderedTicketsForm, 
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
                  'leffalippu/home.html',
                  {
                      'order_form': order_form,
                      'category_formset': category_formset,
                  })

