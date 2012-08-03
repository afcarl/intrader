""" 
Trader class for Pyntrader. Handles position management and executes
trades with a nicer handler on the standard API.

All prices are handled in cents as integers.
"""

from intrade_api import IntradeError
from collections import defaultdict
from decimal import Decimal
from pprint import pformat
from pymongo import DESCENDING
from copy import copy

class TraderError(Exception):
    pass

class Trader():

    def __init__(self, mongo_coll, intrade_api_instance, contract_ids, logger):
        self.data = mongo_coll
        self.intrade = intrade_api_instance
        self.contracts = contract_ids
        self.logger = logger
        self.balance = 0
        self.positions = {}
        self.orders = {}

        self.last_message_check = 0

        self.update_all()

    def __str__(self):
        return '\n'.join(['Pyntrader Trader Class', '', 'Balance',
                          str(self.balance), '',
                          'Positions', pformat(self.positions), '',
                          'Orders', pformat(self.orders), ''])                          

    def handle_errors(fn):
        def wrapper(*args, **kwargs):
            error_count, threshold = 0, 5
            while error_count < threshold:
                try:
                    return fn(*args, **kwargs)
                except ValueError:
                    error_count += 1
                    pass
            raise TraderError(' '.join(['maximum exceptions reached for',
                                        str(fn.__name__)]))
        return wrapper

    def update_all(self):
        """ Updates all three main data categories """
        self.update_balance()
        self.update_positions()
        self.update_orders()

    @handle_errors
    def update_balance(self):
        """ Grabs fresh balance from Intrade """
        self.balance = self.intrade.get_balance()[0]

    @handle_errors
    def update_positions(self):
        """ Grabs fresh positions (completed and current only) from Intrade """
        self.positions = {}
        pos = self.intrade.get_position(self.contracts)
        
        if (not isinstance(pos['position'], list)):
            pos['position'] = [pos['position']]

        for contract in pos['position']:
            if int(contract['quantity']) == 0:
                continue

            this_c = {'quantity': int(contract['quantity']),
                      'cost': int(Decimal(contract['totalCost']) * 100)}
            # approximate, may not be divisible if buying at multiple prices
            this_c['costEach'] = (this_c['cost'] / this_c['quantity']
                                  if this_c['quantity'] != 0 else 0)
            if this_c['quantity'] == 0:
                this_c['position'] = 'none'
            else:
                this_c['position'] = 'long' if this_c['quantity'] > 0 else 'short'

            self.positions[int(contract['@conID'])] = this_c
        
    @handle_errors
    def update_orders(self):
        """ Grabs fresh outstanding orders from Intrade """
        self.orders = defaultdict(list)
        in_orders = self.intrade.get_open_orders()

        if 'order' not in in_orders: # no open orders
            self.orders = {}
            return

        if (not isinstance(in_orders['order'], list)):
            in_orders['order'] = [in_orders['order']]

        for order in in_orders['order']:

            this_o = {'order_id': int(order['@orderID']),
                      'type': str(order['type']),
                      'price': int(Decimal(order['limitprice']) * 10),
                      'quantity': int(order['originalQuantity']),
                      'side': 'buy' if order['side'] == 'B' else 'sell'}

            self.orders[int(order['conID'])].append(this_o)

        self.orders = dict(self.orders)

    @handle_errors
    def check_messages(self):
        """ Returns True if any new messages found, else False. """
        messages = self.intrade.get_messages(self.last_message_check)
        self.last_message_check = int(messages['@timestamp'])
        return True if 'msg' in messages else False

    @handle_errors
    def evaluate_strategy(self):
        """ Checks best possible price for contracts against bid
        parameters specified in configuration file. 

        Returns Strategy object if trade recommended or None. """

        # pull mongo records recorded by price scraper into memory
        bids, offers = {}, {}
        for contract in self.contracts:
            cur = self.data.price.find({'contract_id': contract},
                                       sort = [('last_update', DESCENDING)])
            if not cur:
                return None
            rec = cur[0]

            bids[rec['contract_id']] = rec['bids']
            offers[rec['contract_id']] = rec['offers']

        best_bids = [{'contract': contract,
                      'price': int(Decimal(contract[0]['price']) * 10)}
                      for contract in bids]
        best_offers = [{'contract': contract,
                        'price': int(Decimal(contract[0]['price']) * 10)}
                       for contract in offers]

        agg_bid = sum([x['price'] for x in best_bids])
        agg_offer = sum([x['price'] for x in best_offers])

        # are aggregate offers low enough that we should place FoK orders?
        if agg_offer <= self.intrade.long_max_buy:
            return {'strategy': 'FoK',
                    'bids': self.strategy_fok(bids)}

        # are aggregate bids low enough that we should place our own bids?
        if (agg_bid <= self.intrade.long_max_buy
            and agg_offer <= self.intrade.long_min_sell):

            return {'strategy': 'limit',
                    'bids': self.strategy_limit(bids)}

    def strategy_fok(self, bids):
        """ Determines optimal Fill or Kill order to place based on
        current order book and long_max_buy. Returns dict keyed by
        contract ID with price and quantity to buy with FoK """
        
        all_bids = {}
        for contract in bids:
            cumu_bids, cumu_quantity = [], 0
            for bid in contract:
                cumu_quantity += int(bid['quantity'])
                cumu_bids.append({'price': int(Decimal(bid['price']) * 10),
                                  'quantity': cumu_quantity})
            all_cumu_bids[contract] = cumu_bids

        max_buy = self.balance / 1000

        # how many can we buy right now below our ceiling?
        this_strategy, best_strategy = {}, {}
        for i in xrange(1, max_buy):

            this_price = 0
            for contract in all_cumu_bids:
                for bid in contract:
                    if bid['quantity'] >= i:
                        this_price += bid['price']
                        this_strategy[contract] = {'price': bid['price'],
                                                   'quantity': i}
                        break

            if len(this_strategy) != len(all_cumu_bids):
                return best_strategy

            if this_price > self.long_max_buy:
                break

            best_strategy = copy(this_strategy)

        return best_strategy
        

    def strategy_limit(self, bids):
        """ Determines optimal Limit orders to place based on current
        order book, long_max_buy, and long_min_sell. Returns list of dicts
        with contract, price, and quantity fields """
        return 0
        

            
            
            
        
        
