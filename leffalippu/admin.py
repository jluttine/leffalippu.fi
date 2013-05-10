# Copyright (C) 2013 Jaakko Luttinen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License.
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
Admin for `leffalippu`.
"""

from django.contrib import admin
from leffalippu.models import *

from django.contrib.admin.sites import AdminSite

from admin_views.admin import AdminViews

class OrderedTicketsInline(admin.TabularInline):
    model = OrderedTickets
    extra = 1
    #model = Order.tickets.through

class OrderAdmin(admin.ModelAdmin):
    inlines = (OrderedTicketsInline,)

class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 10

class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'price',
        )

    list_filter = (
        )

    search_fields = (
        'name',
        )
    inlines = (TicketInline,)
    

from django.conf.urls import patterns, include, url
from django.shortcuts import render

class OrderAdmin(AdminViews):
    admin_views = (
        ('Manager', 'manager'),
        )

    list_display = ('encrypted_pk',
                    'date', 
                    'email',
                    'ip',
                    'public_address',
                    'price_in_euros',
                    'price_satoshi',)
    list_filter = ('date',)
    search_fields = (#'encrypted_pk',
                     'email',)

    def manager(self, request, **kwargs):
        # Open orders
        open_order_list = Order.objects.filter(orderstatus=None)

        # Cancelled orders
        cancelled_order_list = Order.objects.filter(orderstatus__status=OrderStatus.CANCELLED)

        # Expired orders
        expired_order_list = Order.objects.filter(orderstatus__status=OrderStatus.EXPIRED)

        # All transactions
        paid_order_list = Order.objects.filter(orderstatus__status=OrderStatus.PAID)

        # All tickets
        ticket_list = Ticket.objects.all().order_by('expires')

        return render(request, 
                      'admin/manager.html',
                      {
                          'ticket_list':      ticket_list,
                          'open_order_list': open_order_list,
                          'cancelled_order_list': cancelled_order_list,
                          'expired_order_list': expired_order_list,
                          'paid_order_list': paid_order_list,
                      })

class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_hash',
        'order',
        'value',
        'input_address',
        'destination_address',
        'confirmations',
        'input_transaction_hash',
        'date',
        )

    list_filter = (
        'date',
        )

    search_fields = (
    #'order',
        'transaction_hash',
        'input_address',
        'destination_address',
        'input_transaction_hash',
        )

        
class TicketAdmin(admin.ModelAdmin):
    list_display = ('number',
                    'category',
                    'price',
                    'expires')

    list_filter = ('category__name', 
                   'expires')

    search_fields = ('number',)
    
## class TicketAdmin(admin.ModelAdmin):
##     def get_urls(self):
##         urls = super(TicketAdmin, self).get_urls()
##         my_urls = patterns('',
##             url(r'^manager/$', self.admin_site.admin_view(self.manager_view),
##                 name='manager'),
##         )
##         return my_urls + urls

##     def manager_view(self, request):
##         # Open orders
##         open_order_list = Order.objects.filter(orderstatus=None)

##         # Cancelled orders
##         cancelled_order_list = Order.objects.filter(orderstatus__status=OrderStatus.CANCELLED)

##         # Expired orders
##         expired_order_list = Order.objects.filter(orderstatus__status=OrderStatus.EXPIRED)

##         # All transactions
##         paid_order_list = Order.objects.filter(orderstatus__status=OrderStatus.PAID)

##         # All tickets
##         ticket_list = Ticket.objects.all().order_by('expires')

##         return render(request, 
##                       'leffalippu/manager.html',
##                       {
##                           'ticket_list':      ticket_list,
##                           'open_order_list': open_order_list,
##                           'cancelled_order_list': cancelled_order_list,
##                           'expired_order_list': expired_order_list,
##                           'paid_order_list': paid_order_list,
##                       })


## site = MyAdminSite()

## site.register(Ticket)
## site.register(Transaction)
## site.register(Category, CategoryAdmin)
## site.register(Order, OrderAdmin)
## site.register(ReservedTickets)

#admin.site.register(Ticket)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(OrderStatus)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderedTickets)
admin.site.register(PaidTicket)
admin.site.register(Transaction, TransactionAdmin)
