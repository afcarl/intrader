import requests
import urllib2 # requests hits a bug on POST responses from Intrade
import xml.etree.ElementTree as xml
from xml.parsers.expat import ExpatError
import xmltodict
from decimal import Decimal
from simplejson import dumps
import ConfigParser
import pytz
from datetime import datetime
from intrader_lib import initLogger

class IntradeError(Exception):
    pass

class MarketHoursError(Exception):
    pass

class Intrade():

    base_get = 'http://api.intrade.com/jsp/XML/MarketData/'
    base_post = 'https://api.intrade.com/xml/handler.jsp'
    test_get = 'http://testexternal.intrade.com/jsp/XML/MarketData/'
    test_post = 'http://testexternal.intrade.com/xml/handler.jsp'

    def __init__(self, config_path = 'intrader.conf'):
        self.extract_config(config_path)
        self.session = self.get_login()['sessionData']
        self.logger = initLogger(__name__, 'debug', email = False)

    def __str__(self):
        prefix = 'SANDBOXED' if self.sandbox else ''
        return ' '.join([prefix, 'Intrade API caller instance with user', self.user,
                         'and session', self.session])

    def extract_config(self, config_path):
        """ Reads config file variables into Intrade object """
        config = ConfigParser.ConfigParser()
        config.read(config_path)

        # sandbox and auth
        self.sandbox = (True if config.get('Sandbox', 'enabled').lower() == 'true'
                        else False)
        if self.sandbox:
            self.user = config.get('Sandbox', 'username')
            self.password = config.get('Sandbox', 'password')
        else:
            self.user = config.get('Auth', 'username')
            self.password = config.get('Auth', 'password')
            
        # market hours
        self.intrade_tz = pytz.timezone(config.get('Intrade', 'timezone'))
        self.market_start = config.get('Intrade', 'market_start')
        self.market_end = config.get('Intrade', 'market_end')

    def keepalive(self):
        """ Reauths if necessary to keep connection alive """
        if (datetime.today() - self.last_auth).seconds >= (60 * 60 * 5):
            self.session = self.get_login()['sessionData']

    def prettyable(fn):
        """ Allows pretty printing of function by passing pretty = True """
        def wrapper(*args, **kwargs):
            if 'pretty' in kwargs and kwargs['pretty'] == True:
                return dumps(fn(*args, **kwargs), indent = 4, sort_keys = False)
            else:
                return fn(*args, **kwargs)
        return wrapper

    def check_market_hours(self):
        """ Raises trading hours error if called outside of trading hours """
        utc_dt = pytz.utc.localize(datetime.utcnow())
        intrade_dt = utc_dt.astimezone(self.intrade_tz)
        current_hm = ''.join([str(intrade_dt.hour), str(intrade_dt.minute)])

        eff_ms, eff_me = int(self.market_start), int(self.market_end)
        eff_curr = int(current_hm)
        # handling for downtime crossing midnight
        if eff_me >= eff_ms:
            if eff_curr >= eff_me or eff_curr <= eff_ms:
                raise MarketHoursError('call cannot occur outside of trading hours')
        elif eff_curr >= eff_me and eff_curr <= eff_ms:
            raise MarketHoursError('call cannot occur outside of trading hours')

    def get_login(self):
        """ Auth """
        self.last_auth = datetime.today()
        login = self.post(params = {'header': {'requestOp': 'getLogin'},
                                   'body': {'membershipNumber': self.user,
                                            'password': self.password}},
                         parse_to_json = True)
        if login['sessionData'] == 'ANONYMOUS':
            raise IntradeError('login failed')
        return login

    def get(self, res, params = None, parse_to_json = True):
        """ HTTP GET to Intrade """
        self.keepalive()
        url = self.test_get if self.sandbox else self.base_get
        while True:
            try:
                r = requests.get(''.join([url, res]), params = params)
                break
            except:
                print 'Request error in Intrader.get logged in Mongo'
                self.logger.error('get.request', exc_info = True)
                pass # this should probably be less infinite
        
        try:
            parsed = xmltodict.parse(r.content)
        except ExpatError:
            try:
                self.logger.error('get.parsexml %s', r.raw, exc_info = True)
            except:
                self.logger.error('get.parsexml could not get raw', exc_info = True)
            raise IntradeError('error parsing GET return from XML')

        for key in parsed.iterkeys():
            if 'error' in parsed[key]:
                raise IntradeError(parsed[key]['error'])

        if parse_to_json:
            return parsed.items()[0][1]
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

        self.keepalive()
        url = self.test_post if self.sandbox else self.base_post

        r = urllib2.Request(url,
                            data = self.make_xml(params),
                            headers = {'content-type': 'text/xml'})
        u = urllib2.urlopen(r)

        parsed = xmltodict.parse(u.read())
        errored = 'errorcode' in parsed['tsResponse']

        if errored:
            print self.make_xml(params)
            raise IntradeError(parsed['tsResponse']['errorcode'])

        if parse_to_json:
            return parsed.items()[0][1]
        else:
            return u.read()

    @prettyable
    def contracts(self, class_id = None, **kwargs):
        """ Active contract info, either all or for specific class """
        if class_id:
            return self.get('XMLForClass.jsp', {'classID': class_id})
        else:
            return self.get('xml.jsp')

    @prettyable
    def prices(self, contract_ids, depth = 5, timestamp = 0, **kwargs):
        """ Current prices posted after timestamp for given contract IDs """
        self.check_market_hours()
        return self.get('ContractBookXML.jsp', {'id': contract_ids,
                                                'depth': depth,
                                                'timestamp': timestamp})

    @prettyable
    def con_info(self, contract_ids, **kwargs):
        """ Lifetime contract info for one contract """
        return self.get('ConInfo.jsp', {'id': contract_ids})

    @prettyable
    def closing_price(self, contract_id, **kwargs):
        """ Historical closing prices for lifetime of one contract """
        if not isinstance(contract_id, (str, int)):
            raise IntradeError('closing_price requires exactly one contract_id (str or int)')
        return self.get('ClosingPrice.jsp', {'conID': contract_id})

    def time_and_sales(self, contract_id):
        # was broken at time of writing, maybe they'll fix it someday
        return None

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
                raise IntradeError('order side must be B or S')
            if ((not isinstance(order_dict['quantity'], int)) or
                order_dict['quantity'] <= 0):
                raise IntradeError('order quantity must be integer greater than zero')
            if order_dict['timeInForce'] not in ['GTC', 'GFS', 'GTT']:
                raise IntradeError('order time_in_force must be GTC, GFS, or GTT')

            # convert prices in cents to prices in probabilities based on $10 contract
            order_dict['limitPrice'] = order_dict['limitPrice'] / float(10)
            if 'touchPrice' in order_dict or order_dict['orderType'] == 'T':
                order_dict['touchPrice'] = order_dict['touchPrice'] / float(10)
        except KeyError:
            raise IntradeError('required field missing from order constructor')
    
        order_str = ''
        for var in ['conID', 'side', 'limitPrice', 'quantity', 'orderType',
                    'timeInForce', 'touchPrice', 'userReference']:
            if var in order_dict:
                order_str = ''.join([order_str, var, '=', str(order_dict[var]), ','])

        return order_str.rstrip(',')

    @prettyable
    def multi_order_request(self, orders, cancel_previous = False, **kwargs):
        """ Submits multiple orders """
        self.check_market_hours()
        return self.post(params = {'header': {'requestOp': 'multiOrderRequest'},
                                   'body': {'cancelPrevious': cancel_previous,
                                            'order': orders,
                                            'sessionData': self.session}})

    @prettyable
    def cancel_multiple_orders(self, orders, **kwargs):
        """ Cancels all open orders previously submitted """
        self.check_market_hours()
        return self.post(params = {'header': {'requestOp': 'cancelMultipleOrdersForUser'},
                                   'body': {'orderID': orders,
                                            'sessionData': self.session}})

    @prettyable
    def cancel_orders(self, contract, types = 'ALL', **kwargs):
        """ Cancels specified type of open orders in one contract """
        self.check_market_hours()
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

    @prettyable
    def cancel_all_in_event(self, event, **kwargs):
        """ Cancels all orders in one event """
        self.check_market_hours()
        return self.post(params = {'header': {'requestOp': 'cancelAllInEvent'},
                                   'body': {'eventID': event,
                                            'sessionData': self.session}})

    @prettyable
    def get_position(self, contracts, **kwargs):
        """ Gets current positions for specified contracts """
        return self.post(params = {'header': {'requestOp': 'getPosForUser'},
                                   'body': {'contractID': contracts,
                                            'sessionData': self.session}})

    @prettyable
    def get_open_orders(self, contract = None, **kwargs):
        """ Gets all of user's open orders for all or specified contract """
        body = {'sessionData': self.session}
        if contract:
            body['contractID'] = contract
        return self.post(params = {'header': {'requestOp': 'getOpenOrders'},
                                   'body': body})

    @prettyable
    def get_orders(self, orders, **kwargs):
        """ Gets information on specified order IDs """
        return self.post(params = {'header': {'requestOp': 'getOrdersForUser'},
                                   'body': {'orderID': orders,
                                            'sessionData': self.session}})
