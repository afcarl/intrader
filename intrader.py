import sys
import pymongo
import intrade_api
import ConfigParser
from simplejson import dumps

def d(json):
    return dumps(json, indent = 4, sort_keys = False)

def main():

    conn = pymongo.Connection()
    data = conn.intrade

    Config = ConfigParser.ConfigParser()
    Config.read('intrader.conf')

    intrade = auth(Config)

    print intrade.get_balance()
    a = intrade.order({'conID': 320111, 'side': 'B', 'limitPrice': 400,
                       'quantity': 1, 'orderType': 'L', 'timeInForce': 'GTC',
                       'userReference': 'ok'})
    b = intrade.order({'conID': 320111, 'side': 'B', 'limitPrice': 450,
                       'quantity': 5, 'orderType': 'L', 'timeInForce': 'GTC',
                       'userReference': 'nope'})
    # print intrade.multi_order_request([a, b])

    print d(intrade.prices('320111'))
    print d(intrade.get_position('320111'))
    print d(intrade.get_open_orders('320111'))
    
    sys.exit()

def auth(conf):
    """ Initializes Intrade object and authenticates for POST requests """
    sandbox = True if conf.get('Sandbox', 'enabled').lower() == 'true' else False

    if sandbox:
        u, p = conf.get('Sandbox', 'username'), conf.get('Sandbox', 'password')
    else:
        u, p = conf.get('Auth', 'username'), conf.get('Auth', 'password')

    return intrade_api.Intrade(u, p, sandbox)

if __name__ == '__main__':
    main()
