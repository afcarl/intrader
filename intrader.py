import sys
import pymongo
import intrade_api
import threading
from simplejson import dumps
import time
from math import floor
from intrader_lib import init_logger
from datetime import datetime
import atexit

class PriceScraper(threading.Thread):
    def __init__(self, data, intrade, contracts):
        threading.Thread.__init__(self)
        self.logger = init_logger(__name__, 'debug')
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
                    if not isinstance(r['contractInfo'], list):
                        r['contractInfo'] = [r['contractInfo']]
                    for rec in r['contractInfo']:
                        rec['@lastUpdateTime'] = r['@lastUpdateTime']
                        self.data.price.save(rec)
                    print ' '.join(['New price data recorded for',
                                    str(self.contracts), 'at',
                                    str(datetime.today())])

            except intrade_api.MarketHoursError:
                print 'Prices call disabled outside of market hours'
            except intrade_api.IntradeError:
                print ' '.join(['Intrade Error in PriceScraper at',
                                str(datetime.today()), 'see Mongo logs'])
                self.logger.error('Intrade Error in PriceScraper', exc_info = True)
            except:
                print ' '.join(['Unexpected Error detected in PriceScraper at',
                                str(datetime.today()), 'see Mongo logs'])
                self.logger.error('Unexpected Error in PriceScraper', exc_info = True)
            finally:
                time.sleep(1)
                pass
    
def main():

    logger = init_logger(__file__, 'debug')
    logger.info('began execution')

    conn = pymongo.Connection()
    data = conn.intrade

    intrade = intrade_api.Intrade()

    for contract_group in [['743474', '743475'],
                           ['639648', '639649'],
                           ['639654', '639655', '639656'],
                           ['639651', '639652', '639653'],
                           ['754568', '754585', '754570', '754569', '754567',
                            '754566', '754571', '754586', '755933'],
                           ['745813', '745814'],
                           ['745822', '745823'],
                           ['745822', '745823'],
                           ['745735'], ['745736']]:
        price_thread = PriceScraper(data, intrade, contract_group)
        price_thread.setDaemon(True)
        price_thread.start()

    while True:
        time.sleep(60)

def cleanup():
    logger = init_logger('cleanup', 'debug')
    logger.info('stopped execution')

if __name__ == '__main__':
    atexit.register(cleanup)
    main()
