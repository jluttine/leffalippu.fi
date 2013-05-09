import urllib2
import simplejson
from django.conf import settings
from django.core.urlresolvers import reverse

def get_json(url):
    """
    Get JSON response from an URL and return it as a nested dictionary.
    """
    req = urllib2.Request(url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    return simplejson.load(f)

def get_bitcoin_address(receiving_address, shared, callback_url):
    blockchain_url = 'https://blockchain.info/api/receive?method=create&address=%s&shared=%g&callback=%s' % (receiving_address, shared, callback_url)

    blockchain_json = get_json(blockchain_url)
    payment_address = blockchain_json['input_address']
    return payment_address

def cents_to_satoshi(cents):
    """
    Convert a value in euros (units=cents) to bitcoins (units=satoshi).

    Satoshis are handled as long integers.
    """
    try: 
        #url = 'http://blockchain.info/ticker'
        ticker_json = get_json('https://data.mtgox.com/api/1/BTCEUR/ticker')
        if ticker_json['result'] != 'success':
            return None
        # Conversion rate: satoshi/cents
        rate = long(1.0e6 / float(ticker_json['return']['buy']['value']))
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
    address = get_bitcoin_address(settings.BITCOIN_ADDRESS,
                                  False,
                                  (settings.CALLBACK_BASEURL +
                                  reverse('pay', args=[order.encrypted_pk])))

    # Get price in bitcoins (units=satoshi)
    price = cents_to_satoshi(order.price())

    if price is None or address is None:
        raise Exception()

    return (address, price)
    
