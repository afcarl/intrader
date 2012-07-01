import sys
import pymongo
import intrade_api
import threading
from simplejson import dumps
import time
from math import floor
from dow_scraper import get_dow

def d(json):
    return dumps(json, indent = 4, sort_keys = False)

class DowScraper(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data

    def run(self):
        while True:
            try:
                dow = get_dow()
                rec = {'_id': int(floor(time.time())), 'l': dow['l'], 'l_cur': dow['l_cur']}
                print 'Saved Dow data'
                self.data.dow.save(rec)
                time.sleep(1)
            except:
                print 'ERROR:', dow
                pass
    
class PriceScraper(threading.Thread):
    def __init__(self, data, intrade, contracts):
        threading.Thread.__init__(self)
        self.data = data
        self.intrade = intrade
        self.contracts = contracts

    def run(self):

        self.last_new = 0
        while True:
            try:
                r = self.intrade.prices(self.contracts, timestamp = self.last_new)
                self.last_new = r['@lastUpdateTime']
                if 'contractInfo' in r:
                    for rec in r['contractInfo']:
                        rec['@lastUpdateTime'] = r['@lastUpdateTime']
                        self.data.price.save(rec)
                    print 'New price data recorded for', self.contracts
                else:
                    'No new price data for', self.contracts
                time.sleep(5)
            except TypeError: # some kind of unicode thing?
                print 'Error in PriceScraper'
                pass
    
def main():

    conn = pymongo.Connection()
    data = conn.intrade

    intrade = intrade_api.Intrade()

    dow_thread = DowScraper(data)
    dow_thread.setDaemon(True)
    dow_thread.start()

    for contract_group in [['743474', '743475'],
                           ['639648', '639649']]:
        price_thread = PriceScraper(data, intrade, contract_group)
        price_thread.setDaemon(True)
        price_thread.start()
    
    # print intrade.get_balance()
    # a = intrade.order({'conID': 320111, 'side': 'B', 'limitPrice': 400,
    #                    'quantity': 1, 'orderType': 'L', 'timeInForce': 'GTC',
    #                    'userReference': 'ok'})
    # b = intrade.order({'conID': 320111, 'side': 'B', 'limitPrice': 450,
    #                    'quantity': 5, 'orderType': 'L', 'timeInForce': 'GTC',
    #                    'userReference': 'nope'})
    # # print intrade.multi_order_request([a, b])

    # print d(intrade.prices('320111'))
    # print d(intrade.get_position('320111'))
    # print d(intrade.get_open_orders('320111'))

    while True:
        time.sleep(60)

if __name__ == '__main__':
    main()
