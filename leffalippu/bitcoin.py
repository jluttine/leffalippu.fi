import urllib2
import simplejson
from django.conf import settings
from django.core.urlresolvers import reverse

from django.http import Http404, HttpResponseRedirect, HttpResponse

from leffalippu.models import Order, Transaction

from django.db.models import Sum

import crypto

from django.conf import settings

callback_crypto = crypto.KeyCrypto(settings.CALLBACK_CHAR8KEY)

def get_json(url):
    """
    Get JSON response from an URL and return it as a nested dictionary.
    """
    req = urllib2.Request(url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    return simplejson.load(f)

def get_bitcoin_address(receiving_address, shared, callback_url):
    """
    Get a new bitcoin address and set a notifier for it.
    """
    blockchain_url = 'https://blockchain.info/api/receive?method=create&address=%s&shared=%g&callback=%s' % (receiving_address, shared, callback_url)

    try:
        blockchain_json = get_json(blockchain_url)
        payment_address = blockchain_json['input_address']
        return payment_address
    except Exception as e:
        print(e)
        return None

def get_rate_mtgox():
    """
    Get EUR/BTC rate from mtgox.com
    """
    ticker_json = get_json('https://data.mtgox.com/api/1/BTCEUR/ticker')
    if ticker_json['result'] != 'success':
        raise Exception("Failed to get conversion rate from MtGox")
    # Conversion rate: satoshi/cents
    return float(ticker_json['return']['buy']['value'])

def get_rate_blockchain():
    """
    Get EUR/BTC rate from blockchain.info
    """
    ticker_json = get_json('http://blockchain.info/ticker')
    return ticker_json['EUR']['buy']

def cents_to_satoshi(cents):
    """
    Convert a value in euros (units=cents) to bitcoins (units=satoshi).

    Satoshis are handled as long integers.
    """
    try: 
        # Conversion rate: satoshi/cents
        fee_fix = 1.0 - settings.BITCOIN_FEE/100.0
        rate = long(1.0e6 / (fee_fix * get_rate_mtgox()))
        #rate = long(1.0e6 / (fee_fix * get_rate_blockchain()))

        # Price in bitcoins (satoshi units)
        satoshi = cents * rate

        # Round to 0.0001BTC or 10000 Satoshi
        satoshi = long(round(satoshi, -4))
        return satoshi
    except:
        return None

def create_payment(order):
    """
    Create a bitcoin address and compute the price in bitcoins for an order.
    """
    # Get payment address
    # NOTE: HARDCODED URL..
    encrypted_pk = callback_crypto.encrypt(order.pk)
    secret = settings.CALLBACK_SECRET
    url = (settings.CALLBACK_BASEURL +
           "/callback/" + 
           encrypted_pk +
           "/?secret=%s" % secret)
    print("Callback URL: %s" % url)
    shared = True
    address = get_bitcoin_address(settings.BITCOIN_ADDRESS,
                                  shared, # shared? True/False
                                  url)

    # Get price in bitcoins (units=satoshi)
    price = cents_to_satoshi(order.price())

    if price is None or address is None:
        raise Exception()

    return (address, price)
    
def callback(request, encrypted_pk):
    """
    A callback for blockchain.info payment system.

    The customer pays to the input address and blockchain.info forwards the
    payment to our destination address.
    """
    
    if request.method != 'GET':
        raise Http404
    
    try:
        # Get the order
        order_pk = callback_crypto.decrypt(encrypted_pk)
        order = Order.objects.get(pk=order_pk)
    except Order.DoesNotExist:
        raise Http404

    # Parse the parameters
    try:
        # Received payment in satoshi
        value = long(request.GET['value'])
        # Address that received the transaction
        input_address = request.GET['input_address']
        # Our destination address
        destination_address = request.GET['destination_address']
        # Number of confirmations
        confirmations = int(request.GET['confirmations'])
        # Tx hash to our destination address
        transaction_hash = request.GET['transaction_hash']
        # Tx hash to the input address
        input_transaction_hash = request.GET['input_transaction_hash']
        # Custom parameter
        secret = request.GET['secret']
    except KeyError:
        print("Missing parameters in the callback")
        raise Http404

    # Check SSL?

    
    # Check secret
    if secret != settings.CALLBACK_SECRET:
        print("Wrong secret key")
        raise Http404

    # Enough confirmations?
    if confirmations < 0:
        print("Not enough confirmations")
        raise Http404
    
    # Store the transaction
    transaction = Transaction(order=order,
                              value=value,
                              input_address=input_address,
                              destination_address=destination_address,
                              confirmations=confirmations,
                              transaction_hash=transaction_hash,
                              input_transaction_hash=input_transaction_hash)
    try:
        transaction.save()
    except Exception as e:
        print(e)
        raise Http404

    print("Payment %.5fBTC received for %s" % (value*1e-8, order))
    
    # Check whether the order is now paid
    total_paid = Transaction.objects.filter(order=order).aggregate(Sum('value'))['value__sum']
    if total_paid >= order.price_satoshi:
        try:
            order.pay()
        except:
            # The order could not be set to paid state. Either the order has
            # already expired or been cancelled, or there is a bug in the system
            # such that there are not enough tickets available
            #
            # TODO/FIXME: Some error message to logs?
            pass

    # Return *ok*
    return HttpResponse("*ok*")
    
