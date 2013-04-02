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
Admin for `leffaliput`.
"""

from django.contrib import admin
from leffaliput import models 

class ReservedTicketsInline(admin.TabularInline):
    model = models.ReservedTickets
    extra = 1
    #model = models.Reservation.tickets.through

class ReservationAdmin(admin.ModelAdmin):
    inlines = (ReservedTicketsInline,)

class TicketInline(admin.TabularInline):
    model = models.Ticket
    extra = 10

class CategoryAdmin(admin.ModelAdmin):
    inlines = (TicketInline,)
    

admin.site.register(models.Ticket)
admin.site.register(models.Transaction)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Reservation, ReservationAdmin)
admin.site.register(models.ReservedTickets)
