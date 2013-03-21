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

# NO! Don't reserve specific tickets when buying! Just reserve the
# amounts and reserve the specific tickets when paid. Otherwise people
# could first reserve tickets, then buy other tickets with more
# expiration time and then cancel the previous ones.

from django.db import models

## class Product(models.Model):
##     name = models.CharField(max_length=100, primary_key=True)
##     price = models.PositiveIntegerField()
    
## class Order(models.Model):
##     email = models.EmailField()
##     products = models.ManyToManyField(Product, through='OrderedProduct')

## class OrderedProduct(models.Model):
##     product = models.ForeignKey(Product)
##     order = models.ForeignKey(Order)
##     quantity = models.PositiveIntegerField()
    




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


class Category(models.Model):
    """
    A class for types of tickets.

    For instance, you can have categories such as "BioRex student
    ticket", "Finnkino ticket" etc.
    """
    
    """ Short name of the ticket """
    name = models.CharField(max_length=100, primary_key=True)
    
    """ Long description of the ticket and how to use """
    description = models.TextField()
    
    """ Current selling price of the tickets in cents """
    price = models.PositiveIntegerField()

    def __unicode__(self):
        return self.name

class Reservation(models.Model):
    """
    Class for handling ordering of tickets.

    When an reservation is created, it is open until it either
    expires, is cancelled or is paid. Tickets should be kept reserved
    for the reservation until it either expires or is cancelled.
    """

    #""" Id of the order used in URL """
    #key = models.CharField(max_length=20, primary_key=True)
    
    """ Timestamp of the order placement """
    date = models.DateTimeField(auto_now_add=True)
    
    """ Email address of the customer """
    email = models.EmailField()
    
    """ IP address from where the reservation was made """
    ip = models.GenericIPAddressField(null=True,
                                      blank=True)
    
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

    """ The content of the reservation """
    tickets = models.ManyToManyField(Category, through='ReservedTickets')
    
    def cancel(self):
        pass

    def expire(self):
        pass

    def pay(self):
        pass

    def __unicode__(self):
        return "%s %s %s" % (self.email, self.date, self.status)

class ReservedTickets(models.Model):
    """
    Intermediate class for specifying the amount of tickets in a reservation
    """

    """ Reservation for which the tickets belong to """
    reservation = models.ForeignKey(Reservation)

    """ Category of the tickets """
    category = models.ForeignKey(Category)

    """ Amount of reserved tickets of this type. """
    amount = models.PositiveIntegerField()

    # It is good to store the price that was agreed upon just in case
    # the price of the tickets is changed in the database in the
    # future
    """ Total price per ticket """
    price = models.PositiveIntegerField()

    class Meta:
        unique_together = (("reservation", "category"),)

class Transaction(models.Model):
    """
    Class for handling payments of tickets.
    """

    """ The reservation which lead to this payment """
    reservation = models.OneToOneField(Reservation, primary_key=True)

    """ Timestamp of the payment """
    date = models.DateTimeField(auto_now_add=True)

    # Note: Tickets belonging to this transaction are defined by
    # ForeignKey in Ticket class.

    # Use custom manager?
    #objects = OrderManager()

    def __unicode__(self):
        return "%s %s" % (self.date, self.reservation)

class Ticket(models.Model):
    """
    A movie ticket.

    The ticket may be either available or buyed.
    """

    """ The order for which this ticket was bought (if any) """
    transaction = models.ForeignKey(Transaction,
                                    blank=True,
                                    null=True,
                                    on_delete=models.SET_NULL)

    """ Price we paid to the movie theater """
    price = models.PositiveIntegerField()

    """ Type of the ticket """
    category = models.ForeignKey(Category)

    """ Serial number or other identification code """
    number = models.CharField(max_length=100)

    """ Last valid day of the ticket """
    expires = models.DateField()

    def __unicode__(self):
        return "%s (%s)" % (self.number, self.category)
