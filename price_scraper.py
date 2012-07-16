""" Grabs prices for contract groups defined in Pyntrader. """

import pymongo
import intrade_api
import threading
import time
from intrader_log_lib import init_logger
from intrader_formatters import format_prices
from datetime import datetime
import atexit

class PriceScraper(threading.Thread):
    def __init__(self, data, intrade, contracts):
        threading.Thread.__init__(self)
        self.logger = init_logger(__name__, 'error')
        self.data = data
        self.intrade = intrade
        self.contracts = contracts
        self.last_new = 0

    def run(self):

        while True:

            try:
                r = self.intrade.prices(self.contracts, timestamp = self.last_new,
                                        depth = 10)
                self.last_new = r['@lastUpdateTime']
                new_info = False
                for contract in format_prices(r):
                    if contract:
                        new_info = True
                        self.data.price.save(contract)
                if new_info:
                    print ' '.join(['New price data recorded for',
                                    str(self.contracts), 'at',
                                    str(datetime.today())])

            except intrade_api.MarketHoursError:
                print 'Prices call disabled outside of market hours'
            except intrade_api.IntradeError:
                print ' '.join(['Intrade Error in PriceScraper at',
                                str(datetime.today()), '... see Mongo logs'])
                self.logger.error('Intrade Error in PriceScraper', exc_info = True)
            except:
                print ' '.join(['Unexpected Error detected in PriceScraper at',
                                str(datetime.today()), '... see Mongo logs'])
                self.logger.error('Unexpected Error in PriceScraper', exc_info = True)
            finally:
                time.sleep(1)
    
def main():

    logger = init_logger(__file__, 'debug', email = False)
    logger.info('began execution')

    conn = pymongo.Connection()
    data = conn.intrade

    intrade = intrade_api.Intrade()

    for contract_group in [rec['contracts'] for rec in data.contract_groups.find()]:
        contracts = [int(contract['id']) for contract in contract_group]
        price_thread = PriceScraper(data, intrade, contracts)
        price_thread.setDaemon(True)
        price_thread.start()

    while True:
        time.sleep(60)

def cleanup():
    logger = init_logger('cleanup', 'info')
    logger.info('stopped execution')

if __name__ == '__main__':
    atexit.register(cleanup)
    main()
