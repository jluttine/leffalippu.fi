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
Models for `leffalippu`.
"""

# NO! Don't reserve specific tickets when buying! Just reserve the
# amounts and reserve the specific tickets when paid. Otherwise people
# could first reserve tickets, then buy other tickets with more
# expiration time and then cancel the previous ones.

from django.db import models

from django.db.models import Count, Sum, Q

#import encrypted_models

#from mail_templated import send_mail

from django.conf import settings

# A cron job for finding expired orders.
# Add to crontab: python manage.py runcrons
#from django_cron import CronJobBase, Schedule
#from mail_templated import send_mail
import datetime
from django.utils import timezone

## class ExpirationCronJob(CronJobBase):
##     RUN_EVERY_MINS = 1 # every minute

##     schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
##     code = 'leffalippu.check_expiration'    # a unique code

##     def do(self):
##         now = timezone.now()
##         delta = datetime.timedelta(0, 60*settings.EXPIRATION_MINUTES)
##         earliest_date = now - delta
##         expired_orders = Order.objects.filter(orderstatus=None,date__lt=earliest_date)
##         for order in expired_orders:
##             try:
##                 expired_status = OrderStatus(order=order, 
##                                              status=OrderStatus.EXPIRED)
##                 expired_status.save()
##                 ## send_mail('email/expire.txt',
##                 ##           {
##                 ##               'order': order,
##                 ##               'EMAIL_ADDRESS': settings.EMAIL_ADDRESS,
##                 ##           },
##                 ##           settings.EMAIL_ADDRESS,
##                 ##           [order.email])
##             except:
##                 pass
        
    
## class CategoryManager(models.Manager):

##     def OLD_with_amount_available(self):
##         # Amount of reserved/buyed tickets
##         category_list = self.annotate(amount_reserved=Sum('orderedtickets__amount'))
##         # Total amount of tickets
##         category_list = category_list.annotate(amount_total=Count('ticket'))
##         # Compute the number of available tickets
##         for category in category_list:
##             if category.amount_reserved:
##                 category.amount_available = category.amount_total - category.amount_reserved
##             else:
##                 category.amount_available = category.amount_total
##         return category_list

class Category(models.Model):
    """
    A class for types of tickets.

    For instance, you can have categories such as "BioRex student
    ticket", "Finnkino ticket" etc.
    """
    
    """ Short name of the ticket """
    name = models.CharField(max_length=100, unique=True)
    
    """ Long description of the ticket and how to use """
    description = models.TextField()
    
    """ Current selling price of the tickets in cents """
    price = models.PositiveIntegerField()

    #objects = CategoryManager()

    def __unicode__(self):
        return self.name

    def amount_available(self):
        amount_total = self.ticket_set.count()
        ordered_tickets = self.orderedtickets_set.filter(Q(order__orderstatus=None) | 
                                                           Q(order__orderstatus__status=OrderStatus.PAID))
        amount_ordered = ordered_tickets.aggregate(Sum('amount'))['amount__sum']
        # Use if clause to avoid None
        if amount_ordered is not None:
            return (amount_total - amount_ordered)
        else:
            return amount_total

    def price_in_euros(self):
        return self.price/100.0 #".2f" % (self.price/100.0)
        
        

## class OrderManager(encrypted_models.EncryptedPKModelManager):
##     pass

    ## def create_order(self, email):
    ##     # Send email with payment instructions
    ##     pass

    ## def check_status(self):
    ##     # Go through orders and check whether some have expired or
    ##     # been paid..
    ##     pass

class Order(models.Model):
#class Order(encrypted_models.EncryptedPKModel):
    """
    Class for handling ordering of tickets.

    When an reservation is created, it is open until it either
    expires, is cancelled or is paid. Tickets should be kept reserved
    for the reservation until it either expires or is cancelled.
    """

    """ Object manager for encrypted PKs """
    #objects = OrderManager()

    """ Timestamp of the order placement """
    date = models.DateTimeField(auto_now_add=True)
    
    """ Email address of the customer """
    email = models.EmailField()
    
    """ IP address from where the reservation was made """
    ip = models.GenericIPAddressField(null=True,
                                      blank=True)
    
    # For bitcoin payment
    public_address = models.CharField(max_length=100, unique=True)

    # TODO/FIXME: Try to create such a payment system that you don't
    # need to store any private keys! Just for security. Ok?
    #private_key = models.CharField(max_length=100, unique=True)
    
    """ The content of the reservation """
    tickets = models.ManyToManyField(Category, through='OrderedTickets')

    """ The EUR price converted to bitcoins (in satoshi units) """
    price_satoshi = models.BigIntegerField()
    
    def price(self):
        total_price = 0
        for tickets in self.orderedtickets_set.all():
            total_price += tickets.amount * tickets.price
        return total_price

    def price_in_euros(self):
        return "%.2f" % (self.price()/100.0,)

    def price_in_bitcoins(self):
        return "%.8f" % (self.price_satoshi * 1e-8)

    def cancel(self):
        pass

    def expire(self):
        pass

    def __unicode__(self):
        return self.encrypted_pk
    #return "%s %s" % (self.email, self.date)

    def pay(self):
        # Only open orders can be paid, so check that orderstatus does not exist.
        try:
            self.status = self.orderstatus.status
        except OrderStatus.DoesNotExist:
            orderstatus = OrderStatus(order=self,
                                      status=OrderStatus.PAID)
            try:
                orderstatus.save()
                self.status = orderstatus.status
            except:
                raise Exception("Order could not be paid. Handle this situation.")

            # Add tickets to it
            for ordered_tickets in self.orderedtickets_set.all(): #OrderedTickets.objects.filter(order=self):
                category = ordered_tickets.category
                amount = ordered_tickets.amount
                tickets = Ticket.objects.filter(category=category,
                                                paidticket=None).order_by('expires')
                if len(tickets) < amount:
                    # This should not happen: A customer has paid for more
                    # tickets than we have available. If this ever
                    # happens, it means there's a bug in this system.
                    raise Exception("Serious bug in the system. Not enough tickets available.")
                amount_given = 0
                for ticket in tickets[:amount]:
                    if amount_given == amount:
                        break
                    paid_ticket = PaidTicket(ticket=ticket, orderstatus=orderstatus)
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
                if PaidTicket.objects.filter(orderstatus=orderstatus).count() != amount:
                    # This should not happen: The system was not able to
                    # provide enough tickets for the customer.
                    raise Exception("Serious bug in the system. Not enough tickets given to the customer.")

            tickets = Ticket.objects.filter(paidticket__orderstatus=orderstatus)
            ## send_mail('email/pay.txt',
            ##           {
            ##               'order': self,
            ##               'tickets': tickets,
            ##               'EMAIL_ADDRESS': settings.EMAIL_ADDRESS,
            ##           },
            ##           settings.EMAIL_ADDRESS,
            ##           [self.email])

class OrderedTickets(models.Model):
    """
    Intermediate class for specifying the amount of tickets in a reservation
    """

    """ Order for which the tickets belong to """
    order = models.ForeignKey(Order)

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
        unique_together = (("order", "category"),)

    def __unicode__(self):
        return "%d x %s @ %s" % (self.amount, self.category, self.order.encrypted_pk)

class Ticket(models.Model):
    """
    A movie ticket.

    The ticket may be either available or buyed.
    """

    """ Price we paid to the movie theater """
    price = models.PositiveIntegerField()

    """ Type of the ticket """
    category = models.ForeignKey(Category)

    """ Serial number or other identification code """
    number = models.CharField(max_length=100)

    """ Last valid day of the ticket """
    expires = models.DateField()

    class Meta:
        unique_together = (("number", "category"),)

    def __unicode__(self):
        return "%s %s (%s)" % (self.category, self.number, self.expires)

class OrderStatus(models.Model):
    order = models.OneToOneField(Order, unique=True)
    date = models.DateTimeField(auto_now_add=True)

    # Status: expired/cancelled/paid
    PAID = 'P'
    CANCELLED = 'C'
    EXPIRED = 'E'
    STATUS_CHOICES = (
        (PAID, 'Paid'),
        (CANCELLED, 'Cancelled'),
        (EXPIRED, 'Expired'),
    )
    """ Current status of the order """
    status = models.CharField(max_length=1,
                              choices=STATUS_CHOICES)
    
    def __unicode__(self):
        return "%s" % (self.get_status_display())
    
class PaidTicket(models.Model):

    """ Ticket that was bought """
    ticket = models.OneToOneField(Ticket, unique=True)

    """ The order for which this ticket was bought (if any) """
    orderstatus = models.ForeignKey(OrderStatus)
    #transaction = models.ForeignKey(Transaction)

    
class Transaction(models.Model):
    """
    A class for representing a bitcoin transaction from a customer.
    """

    """ The order that was paid """
    order = models.ForeignKey(Order)

    """ Received payment in satoshi """
    value = models.BigIntegerField()

    """ Address that received the transaction """
    input_address = models.CharField(max_length=100)

    """ Our destination address """
    destination_address = models.CharField(max_length=100)
    
    """ Number of confirmations """
    confirmations = models.IntegerField()
    
    """ Transaction hash to our destination address """
    transaction_hash = models.CharField(max_length=100,
                                        unique=True)
    
    """ Transaction hash to the input address """
    input_transaction_hash = models.CharField(max_length=100)
    
    """ Timestamp of the transaction """
    date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return "%s" % (self.transaction_hash)
