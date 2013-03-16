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
Models for `leffaliput`.
"""

from django.db import models

class OrderManager(models.Manager):

    # When a status of an order changes, remember to update the ticket
    # too! If the order is expired or cancelled, the ticket must be
    # freed for new orders.

    def create_order(self, email):
        # Send email with payment instructions
        pass

    def check_status(self):
        # Go through orders and check whether some have expired or
        # been paid..
        pass


class Order(models.Model):
    """
    Class for handling orders of tickets.

    When an order is created, it is open until it either expires, is
    cancelled or is paid. Tickets are kept reserved for the order
    until it either expires or is cancelled.
    """

    """ Id of the order used in URL """
    key = models.CharField(max_length=20, primary_key=True)
    """ Timestamp of the order """
    date = models.DateTimeField(auto_now_add=True)
    """ Email address of the customer """
    email = models.EmailField() # maybe optional but recommended?
    # For bitcoin payment
    public_address = models.CharField(max_length=100, unique=True)
    private_key = models.CharField(max_length=100, unique=True)
    
    # Status: open -> expired/cancelled/paid
    OPEN = 'O'
    PAID = 'P'
    CANCELLED = 'C'
    EXPIRED = 'E'
    STATUS_CHOICES = (
        (OPEN, 'Open'),
        (PAID, 'Paid'),
        (CANCELLED, 'Cancelled'),
        (EXPIRED, 'Expired'),
    )
    """ Current status of the order """
    status = models.CharField(max_length=1,
                              choices=STATUS_CHOICES,
                              default=OPEN)

    # Use custom manager?
    objects = OrderManager()

    def cancel(self):
        pass

    def expire(self):
        pass

    def pay(self):
        pass

class TicketType(models.Model):
    """
    A class for types of tickets.
    """
    
    """ Short name of the ticket """
    name = models.CharField(max_length=100, primary_key=True)
    
    """ Long description of the ticket and how to use """
    description = models.TextField()
    
    """ Original price of the ticket in cents """
    price = models.PositiveIntegerField()

    """ Fee for the seller in cents """
    fee = models.PositiveIntegerField()

class Ticket(models.Model):
    """
    Class for a ticket.

    A ticket may be reserved/buyed or available.
    """

    """ The order for which this ticket is reserved or used (if any) """
    order = models.ForeignKey(Order, 
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='tickets')

    """ Type of the ticket """
    tyyppi = models.ForeignKey(TicketType)

    """ Serial number or other identification code """
    number = models.CharField(max_length=100)

    """ Last valid day of the ticket """
    expires = models.DateField()
