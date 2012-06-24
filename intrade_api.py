import requests
import urllib2 # requests hits a bug on POST responses from Intrade
import xml.etree.ElementTree as xml
import xmltodict
from math import ceil
import time
from decimal import *

class Intrade():

    base_get = 'http://api.intrade.com/jsp/XML/MarketData/'
    base_post = 'https://api.intrade.com/xml/handler.jsp'
    test_get = 'http://testexternal.intrade.com/jsp/XML/MarketData/'
    test_post = 'http://testexternal.intrade.com/xml/handler.jsp'

    def __init__(self, user, password, sandbox = False):
        self.user = user
        self.password = password
        self.sandbox = sandbox
        self.session = self.get_login()['tsResponse']['sessionData']

    def get_login(self):
        return self.post(params = {'header': {'requestOp': 'getLogin'},
                                   'body': {'membershipNumber': self.user,
                                            'password': self.password}},
                         parse_to_json = False)


    def __str__(self):
        prefix = 'SANDBOXED' if self.sandbox else ''
        return ' '.join([prefix, 'Intrade API caller instance with user', self.user,
                         'and session', self.session])

    class IntradeError(BaseException):
        pass

    def get(self, res, params = None, parse_to_json = True):
        """ HTTP GET to Intrade """
        url = self.test_get if self.sandbox else self.base_get
        while True:
            try:
                r = requests.get(''.join([url, res]), params = params)
                break
            except:
                pass # this should probably be less infinite

        parsed = xmltodict.parse(r.content)
        for key in parsed.iterkeys():
            if 'error' in parsed[key]:
                raise self.IntradeError(parsed[key]['error'])

        if parse_to_json:
            return parsed
        else:
            return r.content

    def make_xml(self, in_dict):
        """ Dict to XML, requires {'header': {...}, 'body': {...}} """
        root = xml.Element('xmlrequest')
        for key, value in in_dict['header'].iteritems():
            root.attrib[key] = value
        for key, value in in_dict['body'].iteritems():
            if not isinstance(value, list):
                value = [value]
            for list_elem in value:
                elem = xml.SubElement(root, key)
                elem.text = list_elem
        return xml.tostring(root)

    def post(self, params, parse_to_json = True):
        """ HTTP or HTTPS POST to Intrade using XML, uses urllib2 since
        requests hits a prolog error / bug """

        url = self.test_post if self.sandbox else self.base_post

        r = urllib2.Request(url,
                            data = self.make_xml(params),
                            headers = {'content-type': 'text/xml'})
        u = urllib2.urlopen(r)

        parsed = xmltodict.parse(u.read())
        errored = 'errorcode' in parsed['tsResponse']

        if errored:
            print self.make_xml(params)
            raise self.IntradeError(parsed['tsResponse']['errorcode'])

        if parse_to_json:
            return parsed
        else:
            return u.read()
                          
    def contracts(self, class_id = None):
        """ Active contract info, either all or for specific class """
        if class_id:
            return self.get('XMLForClass.jsp', {'classID': class_id})
        else:
            return self.get('xml.jsp')

    def prices(self, contract_ids,
               depth = 5, timestamp = ceil(time.time()) * 1000):
        """ Current prices posted after timestamp for given contract IDs """
        return self.get('ContractBookXML.jsp', {'id': contract_ids,
                                                'depth': depth,
                                                'timestamp': timestamp})

    def con_info(self, contract_ids):
        """ Lifetime contract info for one contract """
        return self.get('ConInfo.jsp', {'id': contract_ids})

    def closing_price(self, contract_id):
        """ Historical closing prices for lifetime of one contract """
        if not isinstance(contract_id, (str, int)):
            raise self.IntradeError('closing_price requires exactly one contract_id (str or int)')
        return self.get('ClosingPrice.jsp', {'conID': contract_id})

    def time_and_sales(self, contract_id):
        # was broken at time of writing, maybe they'll fix it someday
        return None

    def get_login(self):
        """ Auth """
        login = self.post(params = {'header': {'requestOp': 'getLogin'},
                                   'body': {'membershipNumber': self.user,
                                            'password': self.password}},
                         parse_to_json = True)
        if login['tsResponse']['sessionData'] == 'ANONYMOUS':
            raise self.IntradeError('login failed')
        return login

    def get_balance(self):
        """ Available and Frozen balances in USD cents """
        resp = self.post(params = {'header': {'requestOp': 'getBalance'},
                                   'body': {'sessionData': self.session}})
        return (int(Decimal(resp['tsResponse']['available']) * 100),
                int(Decimal(resp['tsResponse']['frozen'])))

    def order(self, order_dict):
        """ Constructs comma-delimited string describing a new order """
        # validation checks before sending request
        try:
            if order_dict['side'] not in ['B', 'S']:
                raise self.IntradeError('order side must be B or S')
            if ((not isinstance(order_dict['quantity'], int)) or
                order_dict['quantity'] <= 0):
                raise self.IntradeError('order quantity must be integer greater than zero')
            if order_dict['timeInForce'] not in ['GTC', 'GFS', 'GTT']:
                raise self.IntradeError('order time_in_force must be GTC, GFS, or GTT')

            # convert prices in cents to prices in probabilities based on $10 contract
            order_dict['limitPrice'] = order_dict['limitPrice'] / float(10)
            if 'touchPrice' in order_dict or order_dict['orderType'] == 'T':
                order_dict['touchPrice'] = order_dict['touchPrice'] / float(10)
        except KeyError:
            raise self.IntradeError('required field missing from order constructor')
    
        order_str = ''
        for var in ['conID', 'side', 'limitPrice', 'quantity', 'orderType',
                    'timeInForce', 'touchPrice', 'userReference']:
            if var in order_dict:
                order_str = ''.join([order_str, var, '=', str(order_dict[var]), ','])

        return order_str.rstrip(',')

    def multi_order_request(self, orders, cancel_previous = False):
        """ Submits multiple orders """
        return self.post(params = {'header': {'requestOp': 'multiOrderRequest'},
                                   'body': {'cancelPrevious': cancel_previous,
                                            'order': orders,
                                            'sessionData': self.session}})

    def cancel_multiple_orders(self, orders):
        """ Cancels all open orders submitted """
        return self.post(params = {'header': {'requestOp': 'cancelMultipleOrdersForUser'},
                                   'body': {'orderID': orders,
                                            'sessionData': self.session}})

    def cancel_orders(self, contract, types = 'ALL'):
        """ Cancels specified type of open orders in one contract """
        if types not in ['ALL', 'BIDS', 'OFFERS']:
            raise IntradeError('cancel_orders requires order type of ALL, BIDS, or OFFERS')
        if types == 'ALL':
            requestOp = 'getCancelAllInContract'
        elif types == 'BIDS':
            requestOp = 'getCancelAllBids'
        elif types == 'OFFERS':
            requestOp = 'getCancelAllOffers'

        return self.post(params = {'header': {'requestOp': requestOp},
                                   'body': {'contractID': contract,
                                            'sessionData': self.session}})

    def cancel_all_in_event(self, event):
        """ Cancels all orders in one event """
        return self.post(params = {'header': {'requestOp': 'cancelAllInEvent'},
                                   'body': {'eventID': event,
                                            'sessionData': self.session}})

    def get_position(self, contracts):
        """ Gets current positions for specified contracts """
        return self.post(params = {'header': {'requestOp': 'getPosForUser'},
                                   'body': {'contractID': contracts,
                                            'sessionData': self.session}})

    def get_open_orders(self, contract = None):
        """ Gets all of user's open orders for all or specified contract """
        body = {'sessionData': self.session}
        if contract:
            body['contractID'] = contract
        return self.post(params = {'header': {'requestOp': 'getOpenOrders'},
                                   'body': body})

    
