""" Executes automated trading strategy based on arbitrage groups. """

import pymongo
import intrade_api
import atexit
from intrader_log_lib import init_logger
from trader import Trader, TraderError
from time import sleep

def main():
    
    while True:

        # make sure we're using current data
        if trader.check_messages():
            trader.update_all()

        # should not be any open orders at the top of the loop
        if trader.orders:
            raise TraderError('encounted unexpected open orders')

        # TODO: reconcile any trades that didn't go how we thought they would
        
        strategy = trader.evaluate_strategy()

        if strategy['strategy'] == 'FoK':
            print 'do stuff'

        elif strategy['strategy'] == 'limit':
            print 'do stuff'

        sleep(1)

def cleanup():
    logger = init_logger('cleanup', 'info')
    logger.info('pyntrader.py stopped execution')

if __name__ == '__main__':
    atexit.register(cleanup)

    logger = init_logger(__file__, 'info', email = False)
    logger.info('pyntrader.py began execution')

    conn = pymongo.Connection()
    data = conn.intrade

    intrade = intrade_api.Intrade()

    groups, contract_ids = {}, set()
    
    for rec in data.contract_groups.find({'trade': True}):
        groups[str(rec['_id'])] = [int(contract['id']) for contract in rec['contracts']]
        [contract_ids.add(int(contract['id'])) for contract in rec['contracts']]

    # override for testing environment
    groups = {'fake_id': [320111, 320112]}
    contract_ids = [320111, 320112]

    # on init, gets current balance, positions, and outstanding trades
    trader = Trader(data, intrade, contract_ids, logger)

    main()




